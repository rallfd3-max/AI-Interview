import numpy as np
import onnxruntime as ort
import subprocess, sys, wave, os

MODEL = r"c:\Users\rising\Desktop\yanjing\mobile\app\src\main\assets\silero_vad.onnx"
WAV = r"c:\Users\rising\Desktop\yanjing\tools\tts_speech.wav"

# 1) Windows TTS 生成真实中文语音
if not os.path.exists(WAV):
    ps = r'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile("c:\Users\rising\Desktop\yanjing\tools\tts_speech.wav")
$s.Speak("今天天气真不错,我们一起去公园散步吧,顺便聊聊天,谈谈工作上的事情")
$s.Dispose()
'''
    subprocess.run(["powershell", "-Command", ps], check=True, timeout=60)

# 2) 读 WAV → 16kHz mono float
with wave.open(WAV, "rb") as w:
    sr_in = w.getframerate()
    ch = w.getnchannels()
    sw = w.getsampwidth()
    raw = w.readframes(w.getnframes())

print(f"TTS WAV: sr={sr_in} ch={ch} width={sw} bytes={len(raw)}")
assert sw == 2
pcm = np.frombuffer(raw, dtype=np.int16)
if ch > 1:
    pcm = pcm.reshape(-1, ch).mean(axis=1).astype(np.int16)

# 线性插值重采样到 16k
target = 16000
if sr_in != target:
    n_out = int(len(pcm) * target / sr_in)
    x = np.linspace(0, len(pcm) - 1, n_out)
    pcm = np.interp(x, np.arange(len(pcm)), pcm.astype(np.float64)).astype(np.int16)

audio = pcm.astype(np.float32) / 32768.0
print(f"resampled: {len(audio)} samples = {len(audio)/16000:.1f}s @16k, peak={np.abs(audio).max():.3f}")

# 3) 帧式推理(与 App 完全一致的喂法)
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])

def run_frames(audio, carry_state=True):
    state = np.zeros((2, 1, 128), dtype=np.float32)
    probs = []
    for i in range(0, len(audio) - 512, 512):
        f = audio[i:i+512].reshape(1, 512).astype(np.float32)
        out = sess.run(None, {"input": f, "state": state, "sr": np.array(16000, dtype=np.int64)})
        probs.append(float(np.asarray(out[0]).flatten()[0]))
        if carry_state:
            state = out[1]
    return np.array(probs)

p_carry = run_frames(audio, carry_state=True)
p_zero = run_frames(audio, carry_state=False)

for name, p in [("状态正常传递", p_carry), ("状态恒为零(模拟App侧state失效)", p_zero)]:
    print(f"\n[{name}] frames={len(p)}")
    print(f"  max={p.max():.4f} avg={p.mean():.4f} >0.5帧数={(p>0.5).sum()} >0.3帧数={(p>0.3).sum()}")
    print(f"  逐秒峰值: {[f'{p[i*31:(i+1)*31].max():.2f}' for i in range(min(len(p)//31, 10))]}")

ok = p_carry.max() > 0.5
print(f"\n结论: {'模型+协议正常,真实语音触发高概率 → 问题在App侧集成' if ok else '模型对真实语音也不响应 → 模型文件有问题,需更换'}")
