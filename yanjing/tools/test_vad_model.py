import onnxruntime as ort
import numpy as np

MODEL = r"c:\Users\rising\Desktop\yanjing\mobile\app\src\main\assets\silero_vad.onnx"
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])

print("=== INPUTS ===")
for i in sess.get_inputs():
    print(f"  {i.name}: shape={i.shape} type={i.type}")
print("=== OUTPUTS ===")
for o in sess.get_outputs():
    print(f"  {o.name}: shape={o.shape} type={o.type}")

# 与 App 相同的喂法: input [1,512] float32, state [2,1,128] zeros, sr scalar int64=16000
state = np.zeros((2, 1, 128), dtype=np.float32)

def run(frames):
    global state
    probs = []
    for f in frames:
        out = sess.run(None, {
            "input": f.reshape(1, -1).astype(np.float32),
            "state": state,
            "sr": np.array(16000, dtype=np.int64),
        })
        prob = out[0]
        # 兼容 [1] / [1,1] / [[..]]
        probs.append(float(np.asarray(prob).flatten()[0]))
        state = out[1]
    return probs

rng = np.random.default_rng(42)
# 1) 3秒纯静音
silence = [np.zeros(512, dtype=np.float32) for _ in range(94)]
p_sil = run(silence)
print(f"\n静音: min={min(p_sil):.4f} max={max(p_sil):.4f} (应为低值)")

# 2) 3秒语音带(模拟人声: 基频+谐波+共振峰包络, 16kHz)
t = np.arange(3 * 16000) / 16000.0
f0 = 140.0
voice = np.zeros_like(t)
for h in range(1, 12):
    voice += (1.0 / h) * np.sin(2 * np.pi * f0 * h * t)
env = 0.5 * (1 + np.sin(2 * np.pi * 3.0 * t))  # 音节节奏 3Hz
voice = voice * env * 0.3
speech_frames = [voice[i*512:(i+1)*512].astype(np.float32) for i in range(94)]
p_sp = run(speech_frames)
print(f"语音: min={min(p_sp):.4f} max={max(p_sp):.4f} avg={np.mean(p_sp):.4f}")
print(f"语音后10帧概率: {[f'{p:.3f}' for p in p_sp[-10:]]}")

verdict = "模型正常(语音概率显著高于静音)" if max(p_sp) > 0.3 and max(p_sp) > 10 * max(p_sil) else "模型输出异常"
print(f"\n结论: {verdict}")
