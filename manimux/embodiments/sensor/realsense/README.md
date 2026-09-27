# RealSense 组件

`RealSenseSensor(SensorBase)` provides pyrealsense2 capture for the camera service
and runtime sensors. Demonstration collection is outside this repository.

## 安装

从仓库根目录安装到已有硬件环境：

```bash
uv pip install --python envs/yam/.venv/bin/python -e '.[realsense]'
```

当前参考环境为 Python 3.12、pyrealsense2 2.58.3.10794。SDK 通过环境安装，不复制
到组件目录。设备使用序列号绑定；`get_device_ids()` 只枚举、不重置设备。
构造组件不导入 pyrealsense2，不打开 USB；`start()` 打开 pipeline，`close()` 释放它。

## 帧与参数

- `read()` 返回 RGB uint8 的 `SensorFrame`；序号来自 RGB 帧，时间为主机接收时间。
- `capture()` 额外返回可选 uint16 深度、米/计数比例、同帧 Unix 与单调时间戳。
- `read_with_timestamp()` exposes RGB/depth/Unix seconds for direct diagnostic use.
  The camera service uses the shared `read() -> SensorFrame` interface.
- `camera_serial` 绑定设备；`width`、`height`、`fps` 显式选择流。
- `enable_depth`、`align_depth`、`flip`、`exposure_us`、`white_balance` 按配置执行。
- The component defaults to 640×480, 30 Hz and RGB only; component YAML explicitly
  selects capture settings.

默认 `background: true`，组件在后台采集，网络服务的请求直接读取最新缓存，
不会为每台相机依次等待下一帧。重复读取同一缓存保持相同的时间戳和序号。
Set `background: false` to call `capture()` synchronously without a capture worker.

保留首帧等待和 `max_frame_age_sec` 停帧处理；SDK 异常直接交给读取方，
不再像旧网络实现一样在后台自动重启 pipeline，不自动更换设备或分辨率。

配置位于 `manimux/configs/embodiment/sensor/realsense.yaml`。YAM 整机示例中相机序列号在
`manimux/configs/local/yam.example.yaml`；旧相机服务的 `device_id` 字段也在服务入口转换。
这两个配置入口调用同一个组件，不保留第二套 RealSense pipeline 实现。

For camera services launched with `--experiment` or `--config`, each entry in the camera preset
can supply `options`, for example `cameras.d405_front.options.exposure_us` and
`white_balance`. These override component capture settings; explicit
station component bindings take precedence. Editing one entry affects only that
stream. Every experiment referencing the preset inherits its overrides.

`exposure_us` selects manual exposure and disables auto exposure; `white_balance`
selects manual white balance and disables auto white balance. Omitting a setting or
using `null` leaves that device control untouched; it does not restore a factory
default. Overrides apply when the camera service starts, not while it is running.

See [camera recipes and the full supported option list](../../../configs/embodiment/sensor/cameras/README.md).
