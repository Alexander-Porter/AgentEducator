import subprocess
import time
import sys

def git_pull_every(seconds):
    while True:
        try:
            # 执行git pull命令
            result = subprocess.run(['git', 'pull'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
            
            # 打印时间和结果
            print(f"[{time.ctime()}] 执行 git pull:")
            print(result.stdout)
            if result.stderr:
                print("错误:", result.stderr)
            
        except Exception as e:
            print(f"[{time.ctime()}] 发生异常: {str(e)}")
        
        # 等待指定秒数
        time.sleep(seconds)

if __name__ == "__main__":
    print("开始自动git pull，每5秒执行一次... (按Ctrl+C停止)")
    try:
        git_pull_every(5)
    except KeyboardInterrupt:
        print("\n停止自动git pull")
        sys.exit(0)