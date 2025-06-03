import os
import time
import argparse
import matplotlib.pyplot as plt
import numpy as np
from keyframe_3 import extract_key_frames, extract_adaptive_key_frames
import loguru
logger = loguru.logger

def benchmark_methods(video_path, output_dir, repeat=3):
    """
    对比传统方法和自适应方法的性能
    
    参数:
        video_path: 测试视频路径
        output_dir: 输出目录
        repeat: 重复测试次数，默认3次
    """
    results = {
        "traditional": [],
        "adaptive": []
    }
    
    # 设置测试参数
    test_params = {
        "num_threads": 8,
        "frame_skip": 100,
        "fine_step": 10,
        "threshold": 0.98,
        "enable_ocr": False,
        "enable_asr": False,
    }
    
    # 为每种方法创建单独的输出目录
    trad_output = os.path.join(output_dir, "traditional")
    adapt_output = os.path.join(output_dir, "adaptive")
    os.makedirs(trad_output, exist_ok=True)
    os.makedirs(adapt_output, exist_ok=True)
    
    # 测试传统方法
    logger.info("测试传统方法性能...")
    for i in range(repeat):
        start_time = time.time()
        extract_key_frames(
            video_path, 
            trad_output, 
            **test_params
        )
        end_time = time.time()
        elapsed = end_time - start_time
        results["traditional"].append(elapsed)
        logger.info(f"传统方法 - 运行 {i+1}: {elapsed:.2f} 秒")
    
    # 测试自适应方法
    logger.info("测试自适应方法性能...")
    for i in range(repeat):
        start_time = time.time()
        extract_adaptive_key_frames(
            video_path, 
            adapt_output, 
            initial_step=30,
            **test_params
        )
        end_time = time.time()
        elapsed = end_time - start_time
        results["adaptive"].append(elapsed)
        logger.info(f"自适应方法 - 运行 {i+1}: {elapsed:.2f} 秒")
    
    # 计算平均时间
    trad_avg = np.mean(results["traditional"])
    adapt_avg = np.mean(results["adaptive"])
    improvement = (trad_avg - adapt_avg) / trad_avg * 100
    
    logger.info(f"传统方法平均时间: {trad_avg:.2f} 秒")
    logger.info(f"自适应方法平均时间: {adapt_avg:.2f} 秒")
    logger.info(f"性能提升: {improvement:.2f}%")
    
    # 绘制性能比较图
    plot_benchmark(results, output_dir)
    
    return results

def plot_benchmark(results, output_dir):
    """
    绘制性能比较图并保存
    """
    plt.figure(figsize=(10, 6))
    
    # 计算平均值和标准差
    trad_avg = np.mean(results["traditional"])
    adapt_avg = np.mean(results["adaptive"])
    trad_std = np.std(results["traditional"])
    adapt_std = np.std(results["adaptive"])
    
    # 条形图
    labels = ['传统方法', '自适应方法']
    means = [trad_avg, adapt_avg]
    errors = [trad_std, adapt_std]
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(x, means, width, yerr=errors, alpha=0.7, 
                  capsize=10, label='处理时间(秒)')
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3点垂直偏移
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # 计算提升百分比
    improvement = (trad_avg - adapt_avg) / trad_avg * 100
    ax.annotate(f'提升: {improvement:.2f}%',
                xy=(1, adapt_avg),
                xytext=(8, -30),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
    
    ax.set_ylabel('处理时间 (秒)')
    ax.set_title('关键帧提取方法性能对比')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'benchmark_results.png'))
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="关键帧提取方法性能基准测试")
    parser.add_argument("video_path", help="测试视频文件路径")
    parser.add_argument("-o", "--output", help="输出目录路径", default="benchmark_results")
    parser.add_argument("-r", "--repeat", type=int, default=3, help="测试重复次数")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video_path):
        logger.error(f"视频文件不存在: {args.video_path}")
        return 1
        
    os.makedirs(args.output, exist_ok=True)
    
    benchmark_methods(args.video_path, args.output, args.repeat)
    
    return 0

if __name__ == "__main__":
    main()
