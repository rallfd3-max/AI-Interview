import subprocess
import os
def convert_to_pcm(input_file, output_file, sample_rate=16000):
    input_file = input_file.replace('\\','/')
    input_file = os.path.abspath(input_file)
    print(input_file)
    """转换音频为PCM格式（16bit, 单声道, 自定义采样率）"""
    cmd = [
        'ffmpeg',
        '-y',  # 覆盖输出文件
        '-i', input_file,  # 输入文件路径
        '-f', 's16le',    # 输出格式：16位小端PCM
        '-ar', str(sample_rate),  # 采样率（16k或8k）
        '-ac', '1',       # 单声道
        '-acodec', 'pcm_s16le',  # 指定PCM编码
        output_file
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print(f"转换成功：{output_file}")
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e.stderr.decode()}")

if __name__ == '__main__':
    # 示例：将input.mp3转为16kHz PCM
    convert_to_pcm("uploads/voice/1.mp3", "output.pcm", sample_rate=16000)