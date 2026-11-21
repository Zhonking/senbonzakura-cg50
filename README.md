# Senbon Zakura for fx-CG50

将《千本樱》视频转换为 CASIO fx-CG50 可播放的黑白视频，并提供可独立运行的原生 G3A 加载项。播放器基于 [oxixes/bad-apple-cg50](https://github.com/oxixes/bad-apple-cg50) 修改，无需 C.Basic。

## 下载与安装

在 Releases 页面下载完整 ZIP，或分别下载以下两个文件：

- `SenbonZakura.g3a`：原生加载项
- `senb.bin`：视频数据，使用独立文件名以避免覆盖其他播放器的 `video.bin`

将两个文件一起复制到 fx-CG50 **存储器根目录**，不要放进子文件夹，也不要修改文件名。然后在主菜单打开 **Senbon Zakura**。

## 操作

- **EXE**：开始播放
- **MENU**：停止播放
- 启动菜单 **F1**：切换实时追赶（卡顿时跳帧）
- 启动菜单 **F2**：切换帧计数显示

播放结束或按 MENU 停止后，切换到其他应用，再重新进入加载项即可播放。

## 当前视频规格

- 时长约 4 分 04 秒
- 2,441 帧，10 fps
- 96×54 像素，4 倍放大至 384×216
- Floyd–Steinberg 抖动黑白画面
- 无声音

实际流畅度取决于计算器读取存储器的速度。G3A 结构、双校验和、视频逐帧容器结构及 ZIP 完整性已检查，尚未在计算器实机上验证。

## 仓库结构

```text
dist/                  可直接安装的 G3A、视频数据与说明
tools/convert_native.py  MP4 → RLE + FastLZ 视频转换器
tools/make_g3a.py        修改参考播放器、图标、路径与校验和
tools/validate_outputs.py 校验 G3A 和视频容器
tools/package_dist.py    生成发布 ZIP
tools/test_encoder.py    编码与压缩链路测试
tools/BadApple.g3a       参考项目的原始加载项
tools/compress.exe       参考项目发布的 Windows FastLZ 压缩器
```

当前版本保留参考播放器的机器码，通过 `make_g3a.py` 修改名称、图标、视频文件名和校验和；并非从 PrizmSDK 重新编译播放器。

## 从其他 MP4 构建

需要 Windows、Python 3、Pillow 和 imageio-ffmpeg。视频源文件不包含在仓库中。

```bash
python -m pip install -r requirements.txt
python tools/make_g3a.py
FFMPEG=$(python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
python tools/convert_native.py input.mp4 --ffmpeg "$FFMPEG" --compressor tools/compress.exe --output dist/senb.bin
python tools/validate_outputs.py dist/SenbonZakura.g3a dist/senb.bin
python tools/package_dist.py
```

输出视频默认为 96×54、10 fps、scale 4。可通过 `--fps`、`--width`、`--height`、`--scale` 和 `--dither` 调整。

## 许可与来源

原项目：[oxixes/bad-apple-cg50](https://github.com/oxixes/bad-apple-cg50)，采用 Unlicense。许可文本见 [LICENSE](LICENSE)。
