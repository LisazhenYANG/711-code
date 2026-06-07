part of '../app_module.dart';

class Shell extends StatefulWidget {
  const Shell({super.key});

  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  _AppState state = const _AppState();
  final _ManyouApi api = const _ManyouApi();

  void selectRouteOption(int index) {
    setState(() => state = state.selectRouteOption(index));
  }

  void confirmSelectedRouteOption() {
    setState(() => state = state.confirmSelectedRouteOption());
  }

  Future<void> triggerHeartbeatAdjustment({
    required String reason,
  }) async {
    final weatherCondition = state.weather?.conditionLabel ?? '晴';
    final prompt = switch (reason) {
      'queue' => '请重新排路线，替换掉当前排队太久的站点，保持顺路、少走路，并优先换成附近更轻松的选择',
      'weather' => '现在天气可能下雨，请重新排路线，把后面的室外点尽量替换成室内点，并保持顺路',
      _ => '请重新排路线，换成更顺路、更轻松的版本',
    };
    try {
      var changed = false;
      final beforeSignature =
          state.routeStops.map((stop) => stop.name).join('|');
      await for (final event in api.streamAiChat(
        message: prompt,
        route: state.routeStops,
        weatherCondition: weatherCondition,
      )) {
        if (!mounted) return;
        if (event.updatedStops.isNotEmpty) {
          final afterSignature =
              event.updatedStops.map((stop) => stop.name).join('|');
          changed = afterSignature != beforeSignature;
          if (changed) {
            setState(
                () => state = state.replaceRouteInPlace(event.updatedStops));
          }
        }
      }
      if (!mounted) return;
      if (!changed) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('附近没有更优替代，先保留当前路线。'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('这次没有成功换线，先保留当前路线。'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    loadBackendState();
  }

  void go(ScreenStage next) {
    setState(() => state = state.goTo(next));
    final effectiveNext = !state.profileLoggedIn && next != ScreenStage.profile
        ? ScreenStage.profile
        : next;
    if (effectiveNext == ScreenStage.guide) {
      unawaited(refreshCurrentLocation());
    }
  }

  void toggleMood(int index) {
    setState(() => state = state.toggleMood(index));
  }

  void toggleBookingSelection(int index) {
    setState(() => state = state.toggleBookingSelection(index));
  }

  Future<void> toggleStopLock(int index) async {
    await runRouteAction('lock', index: index);
  }

  void goToTab(int index) {
    setState(() => state = state.goToTab(index));
  }

  Future<void> deleteStop(int index) async {
    if (state.lockedStopIndexes.contains(index)) {
      setState(() => state = state.showOverlay(_AppOverlay.lockInfo));
      return;
    }
    await runRouteAction('delete', index: index);
  }

  Future<List<_MealRestaurant>> loadMealRestaurants(String slot) async {
    final sourceStops = state.visibleStopIndexes.isNotEmpty
        ? [
            for (final index in state.visibleStopIndexes)
              state.routeStops[index]
          ]
        : state.routeStops;
    final withCoords = [
      for (final stop in sourceStops)
        if (stop.lat != null && stop.lng != null) stop,
    ];
    final anchor = _mealAnchorForSlot(withCoords, slot);
    final centerLat = anchor?.$1 ?? 31.2304;
    final centerLng = anchor?.$2 ?? 121.4737;
    return api.mealRestaurants(lat: centerLat, lng: centerLng, slot: slot);
  }

  Future<List<_RecommendationItem>> loadAddPlaceRecommendations() {
    final sourceStops = state.visibleStopIndexes.isNotEmpty
        ? [
            for (final index in state.visibleStopIndexes)
              state.routeStops[index]
          ]
        : state.routeStops;
    return api.nearbyPlaceRecommendations(sourceStops);
  }

  void applyChatSuggestedRoute(List<_Stop> stops) {
    if (stops.isEmpty) return;
    setState(() => state = state.finishRouteGeneration([
          _RouteOption(
            id: 'chat-route',
            name: '调整后路线',
            label: '最适合你',
            summary: '这是根据你刚才的要求调整后的路线。',
            stops: stops,
            overloadLevel: 'low',
            overloadHint: '轻松',
          ),
        ]));
  }

  (double, double)? _mealAnchorForSlot(List<_Stop> stops, String slot) {
    if (stops.isEmpty) return null;
    final targetMinute = switch (slot) {
      'dinner' => 18 * 60 + 30,
      _ => 12 * 60 + 30,
    };
    final timedStops = <({int minute, _Stop stop})>[];
    for (final stop in stops) {
      final minute = _minuteOfDay(stop.time);
      if (minute != null && stop.lat != null && stop.lng != null) {
        timedStops.add((minute: minute, stop: stop));
      }
    }
    if (timedStops.isEmpty) {
      final first = stops.first;
      return first.lat != null && first.lng != null
          ? (first.lat!, first.lng!)
          : null;
    }
    timedStops.sort((a, b) => a.minute.compareTo(b.minute));

    for (var i = 0; i < timedStops.length - 1; i++) {
      final current = timedStops[i];
      final next = timedStops[i + 1];
      if (targetMinute >= current.minute && targetMinute <= next.minute) {
        final ratio =
            (targetMinute - current.minute) / (next.minute - current.minute);
        final lat =
            current.stop.lat! + ((next.stop.lat! - current.stop.lat!) * ratio);
        final lng =
            current.stop.lng! + ((next.stop.lng! - current.stop.lng!) * ratio);
        return (lat, lng);
      }
    }

    timedStops.sort((a, b) {
      final da = (a.minute - targetMinute).abs();
      final db = (b.minute - targetMinute).abs();
      return da.compareTo(db);
    });
    final nearest = timedStops.first.stop;
    return (nearest.lat!, nearest.lng!);
  }

  int? _minuteOfDay(String label) {
    final match = RegExp(r'(\d{1,2}):(\d{2})').firstMatch(label);
    if (match == null) return null;
    final hour = int.tryParse(match.group(1)!);
    final minute = int.tryParse(match.group(2)!);
    if (hour == null || minute == null) return null;
    return hour * 60 + minute;
  }

  void showOverlay(_AppOverlay overlay) {
    setState(() => state = state.showOverlay(overlay));
  }

  void showStopDetail(int index) {
    setState(() => state = state.showStopDetail(index));
  }

  void showRecommendationDetail(int index) {
    setState(() => state = state.showRecommendationDetail(index));
  }

  void showTransitForStop(int index) {
    setState(() => state = state.showTransitForStop(index));
  }

  void closeOverlay() {
    setState(() => state = state.closeOverlay());
  }

  void toggleRouteChat() {
    setState(() => state = state.toggleRouteChat());
  }

  Stream<_ChatStreamEvent> handleRouteChatCommand(String message) async* {
    final text = message.trim();
    if (text.isEmpty) {
      yield const _ChatStreamEvent(
        message: '你可以直接告诉我想加什么地点，或想怎么调整路线。',
        done: true,
      );
      return;
    }

    final normalized = text.toLowerCase();
    if (text.contains('晚饭') ||
        text.contains('晚餐') ||
        normalized.contains('dinner')) {
      final restaurant = text.contains('烧鸟') ? '鸟啸炭火烧' : '老克勒西餐';
      yield const _ChatStreamEvent(message: '正在安排晚饭...');
      await runRouteAction('add_meal', value: 'dinner|$restaurant');
      yield _ChatStreamEvent(
        message: '已把$restaurant加入晚饭时段，时间放在 18:30。',
        done: true,
      );
      return;
    }
    if (text.contains('中饭') ||
        text.contains('午饭') ||
        text.contains('午餐') ||
        normalized.contains('lunch')) {
      final restaurant = text.contains('杏花') ? '杏花楼' : '沈大成';
      yield const _ChatStreamEvent(message: '正在安排午饭...');
      await runRouteAction('add_meal', value: 'lunch|$restaurant');
      yield _ChatStreamEvent(
        message: '已把$restaurant加入中饭时段，时间放在 12:30。',
        done: true,
      );
      return;
    }
    if (text.contains('少走') || text.contains('减少步行') || text.contains('不想走')) {
      yield const _ChatStreamEvent(message: '正在减少步行路段...');
      await runRouteAction('transit', index: 1, value: 'metro');
      yield const _ChatStreamEvent(
        message: '已优先把下一段交通调整为地铁，减少步行。',
        done: true,
      );
      return;
    }
    if (text.contains('删除') || text.contains('去掉') || text.contains('不要')) {
      final index = _routeIndexFromText(text) ?? state.visibleStopIndexes.last;
      yield _ChatStreamEvent(message: '正在移除第 ${index + 1} 站...');
      await deleteStop(index);
      yield _ChatStreamEvent(
        message: '已尝试移除第 ${index + 1} 站。如果它被锁定，我会保留它并提示你。',
        done: true,
      );
      return;
    }
    if (text.contains('锁定') || text.contains('保留')) {
      final index = _routeIndexFromText(text) ?? 0;
      yield _ChatStreamEvent(message: '正在调整第 ${index + 1} 站的锁定状态...');
      await toggleStopLock(index);
      yield _ChatStreamEvent(
        message: '已切换第 ${index + 1} 站的锁定状态。',
        done: true,
      );
      return;
    }
    try {
      await for (final event in api.streamAiChat(
        message: text,
        route: state.routeStops,
        weatherCondition: state.weather?.conditionLabel ?? '晴',
      )) {
        if (event.intent != 'recommend_place' &&
            event.updatedStops.isNotEmpty &&
            mounted) {
          setState(() {
            state = state.finishRouteGeneration([
              _RouteOption(
                id: 'chat-updated',
                name: '调整后路线',
                label: '最适合你',
                summary: '这是根据你刚才的要求调整后的路线。',
                stops: event.updatedStops,
                overloadLevel: 'low',
                overloadHint: '轻松',
              ),
            ]);
          });
        }
        yield event;
      }
      return;
    } catch (_) {
      yield const _ChatStreamEvent(
        message: '我可以帮你推荐地点、添加地点、安排中饭/晚饭、减少步行、删除或锁定某一站。你可以说：“加武康路”或“安排晚饭”。',
        done: true,
      );
    }
  }

  int? _routeIndexFromText(String text) {
    final match = RegExp(r'第\s*(\d+)\s*站').firstMatch(text);
    if (match != null) {
      final parsed = int.tryParse(match.group(1) ?? '');
      if (parsed != null) {
        return (parsed - 1).clamp(0, state.routeStops.length - 1).toInt();
      }
    }
    if (text.contains('第一')) return 0;
    if (text.contains('第二')) {
      return 1.clamp(0, state.routeStops.length - 1).toInt();
    }
    if (text.contains('第三')) {
      return 2.clamp(0, state.routeStops.length - 1).toInt();
    }
    if (text.contains('最后')) return state.routeStops.length - 1;
    return null;
  }

  Future<void> completeBooking() async {
    final items = state.bookings.isEmpty
        ? state
            .copyWith(bookings: state._bookingsFromStops(state.routeStops))
            .bookings
        : state.bookings;
    try {
      final nextBookings = await api.checkoutBookings(items);
      if (!mounted) return;
      setState(() => state = state.updateBookings(nextBookings));
    } catch (_) {
      if (!mounted) return;
      setState(() => state = state.completeBooking());
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('预约接口暂时不可用，已先保留本地支付状态。'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  void loginProfile(String phone) {
    setState(() => state = state.loginProfile(phone));
  }

  void nextGuideStop() {
    if (state.guideStopIndex >= state.visibleStopIndexes.length - 1) {
      setState(() {
        state = state.copyWith(
          hasArchivedPlan: true,
          stage: ScreenStage.history,
        );
      });
      unawaited(runRouteAction('archive'));
      return;
    }
    setState(() => state = state.nextGuideStop());
    unawaited(refreshCurrentLocation());
  }

  Future<void> refreshCurrentLocation() async {
    setState(() => state = state.startLocating());
    final result = await fetchCurrentLocation();
    if (!mounted) return;
    if (result.hasLocation) {
      setState(
          () => state = state.updateCurrentLocation(result.lat!, result.lng!));
      return;
    }
    setState(() => state = state.failCurrentLocation(
          result.error ?? '定位失败，请稍后再试。',
        ));
  }

  Future<void> runRouteAction(
    String action, {
    int? index,
    String value = '',
    int? recommendationIndex,
    List<String> priorities = const [],
  }) async {
    try {
      final payload = await api.routeAction(
        action: action,
        route: state.routeStops,
        lockedIndexes: state.lockedStopIndexes,
        hiddenIndexes: state.hiddenStopIndexes,
        index: index,
        value: value,
        recommendationIndex: recommendationIndex,
        priorities: priorities,
      );
      if (!mounted) return;
      setState(() => state = state.applyRoutePayload(payload));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('后端动作暂时失败，请确认 backend 已启动。'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> loadBackendState() async {
    try {
      final results = await Future.wait<Object>([
        api.dashboard(),
        api.profile('demo'),
      ]);
      if (!mounted) return;
      setState(() {
        state = state
            .applyDashboard(results[0] as Map<String, dynamic>)
            .applyProfile(results[1] as _UserProfileData);
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        state = state.copyWith(
          bookings: state.bookings.isEmpty
              ? state._bookingsFromStops(state.routeStops)
              : state.bookings,
        );
      });
    }
  }

  Future<void> generateRoute({String freeText = ''}) async {
    if (state.routeLoading) return;
    final moods = [
      for (final index in state.selectedMoodIndexes)
        if (index >= 0 && index < _moodOptions.length)
          _moodOptions[index].title,
    ];
    final discoverItems = _discoverItemsFor(moods, freeText);

    setState(() => state = state.startRouteGeneration());
    try {
      final options = await api.generateRouteOptions(
        moods: moods,
        discoverItems: discoverItems,
        freeText: freeText,
      );
      if (!mounted) return;
      if (options.isEmpty) {
        setState(() => state = state.failRouteGeneration());
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('这次规划没有生成可用路线，请换个偏好再试一次。'),
            behavior: SnackBarBehavior.floating,
          ),
        );
        return;
      }
      setState(() => state = state.finishRouteGeneration(options));
    } catch (error) {
      if (!mounted) return;
      setState(() => state = state.failRouteGeneration());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('规划服务暂时不可用：$error'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  List<String> _discoverItemsFor(List<String> moods, String freeText) {
    final items = <String>[];

    void add(String value) {
      if (!items.contains(value)) items.add(value);
    }

    for (final mood in moods) {
      switch (mood) {
        case '静下来':
          add('窗边咖啡');
          add('图书馆');
          add('草坪时光');
          break;
        case '休闲娱乐':
          add('DIY工坊');
          add('剧本杀');
          add('私人影院');
          break;
        case '热门打卡':
          add('网红地标');
          add('特色景区');
          add('文化艺术');
          break;
        case '购物':
          add('设计师店');
          add('独立品牌');
          add('古着vintage');
          break;
        case '身心焕新':
          add('SPA护理');
          add('按摩足疗');
          add('美容');
          break;
        case '运动':
          add('瑜伽健身');
          add('攀岩');
          add('球类运动');
          break;
      }
    }

    if (freeText.contains('咖啡')) add('窗边咖啡');
    if (freeText.contains('展') || freeText.contains('艺术')) add('文化艺术');
    if (freeText.contains('书') || freeText.contains('阅读')) add('图书馆');
    if (freeText.contains('手作') || freeText.contains('DIY')) add('DIY工坊');
    if (freeText.contains('桌游')) add('剧本杀');
    if (freeText.contains('影院') || freeText.contains('电影')) add('私人影院');
    if (freeText.contains('逛街') || freeText.contains('买')) add('设计师店');
    if (freeText.contains('按摩') || freeText.contains('spa')) add('SPA护理');
    if (freeText.contains('健身') || freeText.contains('运动')) add('瑜伽健身');

    return items.take(3).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFFFF8F3), Color(0xFFFDF4FF)],
          ),
        ),
        child: Stack(
          children: [
            const _AmbientBackground(),
            Center(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final phone = constraints.maxWidth >= 520;
                  final phoneChild = Stack(
                    children: [
                      _AppContent(
                        state: state,
                        onMood: toggleMood,
                        onGo: go,
                        onToggleLock: toggleStopLock,
                        onDeleteStop: deleteStop,
                        onShowOverlay: showOverlay,
                        onShowStopDetail: showStopDetail,
                        onShowTransitForStop: showTransitForStop,
                        onShowRecommendationDetail: showRecommendationDetail,
                        onToggleRouteChat: toggleRouteChat,
                        onRouteChatCommand: handleRouteChatCommand,
                        onApplyChatSuggestedRoute: applyChatSuggestedRoute,
                        onGenerateRoute: generateRoute,
                        onSelectRouteOption: selectRouteOption,
                        onConfirmSelectedRoute: confirmSelectedRouteOption,
                        onLogin: loginProfile,
                        onNextGuideStop: nextGuideStop,
                        onToggleBookingSelection: toggleBookingSelection,
                        onRefreshCurrentLocation: refreshCurrentLocation,
                        onHeartbeatAdjust: triggerHeartbeatAdjustment,
                      ),
                      if (state.stage.showsPrimaryTabs &&
                          !(state.stage == ScreenStage.profile &&
                              !state.profileLoggedIn))
                        Align(
                          alignment: Alignment.bottomCenter,
                          child: _BottomTabs(
                            selected: state.selectedTabIndex,
                            compact: !phone,
                            onTap: goToTab,
                          ),
                        ),
                      _AppOverlays(
                        state: state,
                        onGo: go,
                        onShowOverlay: showOverlay,
                        onClose: closeOverlay,
                        onRestoreStops: () => runRouteAction('restore'),
                        onRouteAction: runRouteAction,
                        onCompleteBooking: completeBooking,
                        onLoadMealRestaurants: loadMealRestaurants,
                        onLoadAddPlaceRecommendations:
                            loadAddPlaceRecommendations,
                      ),
                    ],
                  );
                  final child = _PhoneSurface(
                    showFrame: phone,
                    child: phoneChild,
                  );
                  return phone ? child : SizedBox.expand(child: child);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PhoneSurface extends StatelessWidget {
  const _PhoneSurface({required this.child, required this.showFrame});

  final Widget child;
  final bool showFrame;

  @override
  Widget build(BuildContext context) {
    if (!showFrame) return child;
    return Container(
      width: 390,
      height: 844,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(52),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFF8F3), Color(0xFFFDF4FF)],
        ),
        boxShadow: [
          BoxShadow(
              color: const Color(0xFFEBD2C4).withValues(alpha: .8),
              spreadRadius: 8),
          BoxShadow(
              color: const Color(0xFFD8C0B4).withValues(alpha: .55),
              spreadRadius: 13),
          BoxShadow(
            color: const Color(0xFF8C3C14).withValues(alpha: .16),
            blurRadius: 80,
            offset: const Offset(0, 42),
          ),
        ],
      ),
      child: child,
    );
  }
}
