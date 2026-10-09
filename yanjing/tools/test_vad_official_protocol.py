import numpy as np
import onnxruntime as ort
import wave

MODEL = r"c:\Users\rising\Desktop\yanjing\mobile\app\src\main\assets\silero_vad.onnx"
WAV = r"c:\Users\rising\Desktop\yanjing\tools\tts_speech.wav"

with wave.open(WAV, "rb") as w:
    sr_in, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
pcm = np.frombuffer(raw, dtype=np.int16)
if ch > 1:
    pcm = pcm.reshape(-1, ch).mean(axis=1).astype(np.int16)
if sr_in != 16000:
    n_out = int(len(pcm) * 16000 / sr_in)
    x = np.linspace(0, len(pcm) - 1, n_out)
    pcm = np.interp(x, np.arange(len(pcm)), pcm.astype(np.float64)).astype(np.int16)
audio = pcm.astype(np.float32) / 32768.0

sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])

# 官方协议(OnnxWrapper.__call__): input = 64样本上文 + 512新样本 = 576
state = np.zeros((2, 1, 128), dtype=np.float32)
context = np.zeros(64, dtype=np.float32)
probs = []
for i in range(0, len(audio) - 512, 512):
    chunk = audio[i:i+512]
    x_in = np.concatenate([context, chunk]).reshape(1, 576).astype(np.float32)
    out, new_state = sess.run(None, {
        "input": x_in,
        "state": state,
        "sr": np.array(16000, dtype=np.int64),
    })
    probs.append(float(np.asarray(out).flatten()[0]))
    state = new_state
    context = chunk[-64:]  # 官方: context = x[..., -64:],即当前帧尾部64样本

p = np.array(probs)
print(f"官方协议(64上文+512新=576): frames={len(p)}")
print(f"  max={p.max():.4f} avg={p.mean():.4f} >0.5帧数={(p>0.5).sum()} >0.8帧数={(p>0.8).sum()}")
print(f"  逐秒峰值: {[f'{p[i*31:(i+1)*31].max():.2f}' for i in range(min(len(p)//31, 10))]}")
print(f"\n结论: {'协议正确,语音正常触发 → 修App端喂法即可' if p.max() > 0.5 else '仍异常,需进一步排查'}")
