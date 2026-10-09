# 眼镜与人脸服务联调（2026-10-09）

服务器：`ws://172.20.10.5:18081/ws/recognition`。IP 随电脑网络改变。

## 当前客户端

发送 JSON 文本帧：

```json
{"type":"recognize","request_id":"photo-001","device_id":"phone-001","session_id":"session-001","image_format":"jpeg","stable_frames":1,"image_base64":"完整 JPEG 的 Base64"}
```

周期拍照采用单帧确认，不依赖默认三帧窗口。客户端只用本地人脸检测决定是否上传，完整照片交给后端重新检测，不传裁剪框。

返回 `recognition_result`，人员位于 `person.person_id/name/school/major/description`。仅 `success=true`、`matched=true` 且非未确认状态时显示人物卡。`PENDING_CONFIRMATION` 保留已确认卡片，其他正常未匹配结果回待机。错误代码位于 `error.code`。

## 已安装旧版客户端兼容

后端支持 `face/img`，忽略旧版含义不一致的数组框，在原图检测。采用单帧确认；匹配成功返回旧版 `person_info`，未匹配返回 `error`，其中 `code=unknown_face`。`event/person_left` 转为清除会话；设备标识可从 `X-Device-Id` 读取。HTTP API 不变。

心跳 `ping` 返回 `pong`；`person_left` 返回 `clear`。音频不由人脸服务识别，返回 `error/UNSUPPORTED_MESSAGE_TYPE`，不影响后续照片及心跳。

## 接收证据

服务器出现 `Glasses image received` 表示收到通过字段校验的图片消息，包含 request_id、协议类型和 Base64 长度，不记录照片内容。
`Recognition completed` 表示照片处理完成，match_result 记录结果：空库为 `NO_REGISTERED_FACES`、无人脸为 `NO_FACE`。
`Invalid WebSocket message` 记录消息类型与无敏感值的字段校验原因，不能直接认定照片成功接收。

手机日志依次检查“收到眼镜照片”“已上传待识别照片”“下行原始”。USB 接上电脑不代替手机与眼镜 CXR-L 授权、相机权限和已打开的眼镜界面。

## 本轮验证

后端 pytest：73 passed、4 skipped（未开启可选真实模型/照片集成测试）。协议业务测试使用模拟模型，不能当作实机拍摄成功或识别准确率证明。
客户端新增嵌套人物解析、未匹配/失败/未确认禁止出卡、单帧参数测试。修复版 0.1.1（versionCode=2）已成功构建，43 项客户端单元测试全部通过，APK 签名验证通过；文件见 `yanjing/dist/glasses-client-0.1.1-debug.apk`，哈希及构建结果见同目录 `build-info.json`。未执行手机安装验收。新调试签名不同于原 APK，无法覆盖旧签名版本，需要用户自行卸载旧版后安装并重新授权。源码改动不会自动更新已安装手机应用。
