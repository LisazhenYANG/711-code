# 慢游 Flutter 前端

这个目录是根据 `../frontend.html` 还原的 Flutter 高保真核心流程原型。

## 已实现

- 390x844 手机壳预览，桌面端居中显示，移动端全屏显示
- 粘土风格背景、卡片、按钮、标签、底部导航
- 首页计划卡 / 空状态
- 心情选择页
- 晚游 Agent 推荐路线页
- 路线地图、站点锁定、附近推荐
- 出发前预约清单
- 我的页偏好和开关展示

## 运行

当前机器的 shell 没有检测到 `flutter` / `dart` 命令。配置 Flutter 后，在本目录运行：

```bash
flutter pub get
flutter run -d chrome
```

如果要补齐 iOS / Android 平台目录，可以在本目录执行：

```bash
flutter create . --platforms=ios,android,web
```

然后保留现有 `lib/main.dart` 即可继续运行。
