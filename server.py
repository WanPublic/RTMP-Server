import os
import subprocess
import sys

VIDEOS_ROOT = "videos"
RTMP_URL_TEMPLATE = "rtmp://127.0.0.1:1935/live/{channel}"

def loop_push_channel(channel):
    channel_dir = os.path.join(VIDEOS_ROOT, channel)
    if not os.path.isdir(channel_dir):
        print(f"Channel directory not found: {channel_dir}")
        return
    videos = [f for f in os.listdir(channel_dir) if f.lower().endswith('.mp4')]
    videos.sort()
    if not videos:
        print(f"No videos found in {channel_dir}")
        return
    # 生成所有视频的循环播放列表
    video_paths = [os.path.join(channel_dir, v) for v in videos]
    playlist_path = os.path.join(channel_dir, 'playlist.txt')
    all_video_path = os.path.join(channel_dir, 'all.mp4')
    # 生成playlist.txt（只写文件名）
    with open(playlist_path, 'w') as f:
        for v in videos:
            f.write(f"file '{v}'\n")
    # 拼接所有视频为all.mp4
    concat_cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'playlist.txt', '-c', 'copy', 'all.mp4'
    ]
    print(f"Concatenating videos into {all_video_path} ...")
    subprocess.run(concat_cmd, check=True, cwd=channel_dir)  # 关键：cwd=channel_dir
    # 无限循环推流all.mp4
    rtmp_url = RTMP_URL_TEMPLATE.format(channel=channel)
    print(f"Pushing {all_video_path} to {rtmp_url} (infinite loop)")
    while True:
        cmd = [
            "ffmpeg", "-re", "-stream_loop", "-1", "-i", "all.mp4",
            "-vf", "scale=1920:1080,fps=60",
            "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k",
            "-f", "flv", rtmp_url
        ]
        proc = subprocess.Popen(cmd, cwd=channel_dir)
        proc.wait()  # 如果ffmpeg异常退出则重启循环

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) < 2:
        print("Usage: python loop_push.py <channel>")
        sys.exit(1)
    loop_push_channel(sys.argv[1])
