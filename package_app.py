import os
import shutil
import subprocess

# 获取Vosk目录
import vosk
vosk_dir = os.path.dirname(vosk.__file__)

# 创建临时目录
if not os.path.exists('temp_dist'):
    os.makedirs('temp_dist')

# 使用PyInstaller打包（不处理Vosk DLL）
subprocess.run([
    'pyinstaller',
    '--onedir',
    '--add-data', 'vosk_model;vosk_model',
    '--name', '语音转文字_final',
    'speech_to_text_gui.py'
], check=True)

# 复制整个Vosk目录到dist目录
final_dist_dir = os.path.join('dist', '语音转文字_final')

# 复制Vosk Python库到内部目录
target_vosk_dir = os.path.join(final_dist_dir, '_internal', 'vosk')
if not os.path.exists(target_vosk_dir):
    os.makedirs(target_vosk_dir)

# 复制Vosk目录中的所有文件
for file in os.listdir(vosk_dir):
    src = os.path.join(vosk_dir, file)
    dst = os.path.join(target_vosk_dir, file)
    if os.path.isfile(src):
        shutil.copy2(src, dst)
    elif os.path.isdir(src):
        if file not in ['__pycache__', 'transcriber']:  # 跳过不必要的目录
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

# 确保vosk_model文件夹被复制到可执行文件所在目录
model_src = 'vosk_model'
model_dst = os.path.join(final_dist_dir, 'vosk_model')
if os.path.exists(model_dst):
    shutil.rmtree(model_dst)
shutil.copytree(model_src, model_dst)

# 创建批处理文件，用于正确运行程序
run_batch_file = os.path.join(final_dist_dir, '运行语音转文字.bat')
with open(run_batch_file, 'w') as f:
    f.write('@echo off\n')
    f.write('cd /d "%~dp0"\n')  # 切换到脚本所在目录
    f.write('start "" "语音转文字_final.exe"\n')
    f.write('exit\n')

print(f"打包完成！可执行文件位置：{final_dist_dir}")
print(f"Vosk库已复制到：{target_vosk_dir}")
print(f"模型文件夹已复制到：{model_dst}")
print(f"请运行批处理文件：{run_batch_file}")
