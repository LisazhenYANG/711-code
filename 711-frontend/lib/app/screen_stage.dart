part of '../app_module.dart';

enum ScreenStage {
  home,
  mood,
  agent,
  route,
  execute,
  ticket,
  history,
  archiveDetail,
  discover,
  prompt,
  freeChat,
  guide,
  profile,
}

extension _ScreenStageChrome on ScreenStage {
  bool get showsPrimaryTabs => switch (this) {
        ScreenStage.home ||
        ScreenStage.mood ||
        ScreenStage.discover ||
        ScreenStage.prompt ||
        ScreenStage.profile =>
          true,
        _ => false,
      };
}
