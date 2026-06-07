part of '../../app_module.dart';

class _TicketScreen extends StatelessWidget {
  const _TicketScreen({required this.bookings, required this.onGo});

  final List<_BookingItem> bookings;
  final ValueChanged<ScreenStage> onGo;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('ticket'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '返回', onTap: () => onGo(ScreenStage.home)),
          const SizedBox(height: 12),
          const Text('票券与预约',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 14),
          if (bookings.isEmpty)
            const _ClayCard(
              child: Text('还没有票券或预约',
                  style:
                      TextStyle(color: _inkSoft, fontWeight: FontWeight.w700)),
            )
          else
            for (final booking in bookings)
              _BookingRow(
                icon: booking.icon,
                title: booking.name,
                sub: booking.subtitle,
                status: booking.statusText,
                done: booking.done,
              ),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _HistoryScreen extends StatelessWidget {
  const _HistoryScreen({
    required this.hasArchivedPlan,
    required this.plan,
    required this.stops,
    required this.onGo,
  });

  final bool hasArchivedPlan;
  final _PlanSummary? plan;
  final List<_Stop> stops;
  final ValueChanged<ScreenStage> onGo;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('history'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '返回', onTap: () => onGo(ScreenStage.home)),
          const SizedBox(height: 12),
          const Text('历史行程',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 14),
          if (hasArchivedPlan)
            _HistoryMiniCard(
              title: plan?.title ?? '已完成路线',
              icons: stops.take(3).map((stop) => stop.icon).join(' '),
              count: stops.length,
              onTap: () => onGo(ScreenStage.archiveDetail),
            )
          else
            const _ClayCard(
                child: Text('完成规划并生成存档后，旅程会出现在这里',
                    style: TextStyle(
                        color: _inkSoft, fontWeight: FontWeight.w700))),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _ArchiveDetailScreen extends StatelessWidget {
  const _ArchiveDetailScreen({
    required this.bookings,
    required this.stops,
    required this.onGo,
  });

  final List<_BookingItem> bookings;
  final List<_Stop> stops;
  final ValueChanged<ScreenStage> onGo;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('archive'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '历史', onTap: () => onGo(ScreenStage.history)),
          const SizedBox(height: 12),
          Text(stops.take(3).map((stop) => stop.icon).join(' '),
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 14),
          _ClayCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('📋 今日执行总览',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                for (final booking in bookings)
                  _TodoLine(done: booking.done, label: booking.name),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _RoutePreviewCard(
              stops: stops, onConfirm: () => onGo(ScreenStage.guide)),
          const SizedBox(height: 14),
          _PrimaryButton(
              label: '🚀 开始出发 →', onTap: () => onGo(ScreenStage.guide)),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _DiscoverScreen extends StatelessWidget {
  const _DiscoverScreen({
    required this.recommendations,
    required this.onGo,
    required this.onShowRecommendationDetail,
  });

  final List<_RecommendationItem> recommendations;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<int> onShowRecommendationDetail;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('discover'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '首页', onTap: () => onGo(ScreenStage.home)),
          const SizedBox(height: 12),
          const Text('发现附近灵感',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 14),
          for (var i = 0; i < recommendations.length; i++)
            _SheetAction(
              icon: recommendations[i].icon,
              title: recommendations[i].title,
              sub: recommendations[i].subtitle,
              onTap: () => onShowRecommendationDetail(i),
            ),
          if (recommendations.isEmpty)
            const _ClayCard(
              child: Text('正在获取附近灵感…',
                  style:
                      TextStyle(color: _inkSoft, fontWeight: FontWeight.w700)),
            ),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _PromptScreen extends StatelessWidget {
  const _PromptScreen({required this.onGo});

  final ValueChanged<ScreenStage> onGo;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('prompt'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '返回', onTap: () => onGo(ScreenStage.home)),
          const SizedBox(height: 12),
          const Text('编辑后发送给 Agent',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          const SizedBox(height: 14),
          const _ClayCard(
            color: _card2,
            child: Text(
              '今天下午在上海虹口区，2个人，想要慢悠悠、少排队、有一点艺术感和咖啡休息。请帮我规划 3 个地点，并提醒需要预约的项目。',
              style: TextStyle(
                  color: _inkMid, height: 1.5, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(height: 14),
          _PrimaryButton(
              label: '发送给晚晚 →', onTap: () => onGo(ScreenStage.agent)),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _FreeChatScreen extends StatefulWidget {
  const _FreeChatScreen({
    required this.routeLoading,
    required this.stops,
    required this.onGo,
    required this.onShowOverlay,
    required this.onGenerateRoute,
  });

  final bool routeLoading;
  final List<_Stop> stops;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final Future<void> Function({String freeText}) onGenerateRoute;

  @override
  State<_FreeChatScreen> createState() => _FreeChatScreenState();
}

class _FreeChatScreenState extends State<_FreeChatScreen> {
  final TextEditingController _controller = TextEditingController();
  static const _presetQuestions = [
    '今天下午虹口区，两个人，想少走路',
    '想看展和喝咖啡，帮我安排轻松一点',
    '预算 200 以内，不想排队太久',
    '想要出片一点，也要有吃饭安排',
  ];
  final List<_ChatMessage> _messages = const [
    _ChatMessage(
      fromUser: false,
      text: '我是晚晚。你可以直接告诉我：去哪、几个人、什么时候、想怎么玩、有什么不想要的。我会边聊边帮你整理路线。',
    ),
  ].toList();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    _sendText(text);
  }

  void _sendPreset(String text) {
    _controller.clear();
    _sendText(text);
  }

  void _sendText(String text) {
    if (text.isEmpty || widget.routeLoading) return;
    setState(() {
      _messages.add(_ChatMessage(fromUser: true, text: text));
      _messages.add(_ChatMessage(
        fromUser: false,
        text: '收到。我正在调用规划 Agent，按「$text」生成一版真实路线。',
      ));
      _controller.clear();
    });
    unawaited(widget.onGenerateRoute(freeText: text));
  }

  @override
  Widget build(BuildContext context) {
    final hasUserMessage = _messages.any((message) => message.fromUser);

    return Padding(
      key: const ValueKey('free-chat'),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 18),
      child: Column(
        children: [
          Row(
            children: [
              _TopBack(label: '', onTap: () => widget.onGo(ScreenStage.home)),
              const SizedBox(width: 10),
              const CircleAvatar(
                radius: 18,
                backgroundColor: _brown,
                child: Text('晚',
                    style: TextStyle(
                        color: Colors.white, fontWeight: FontWeight.w900)),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('晚晚 Chatbot',
                        style: TextStyle(
                            fontSize: 18, fontWeight: FontWeight.w900)),
                    Text('自由规划 · 直接输入你的想法',
                        style: TextStyle(
                            color: _inkSoft,
                            fontSize: 12,
                            fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _ClayCard(
              padding: const EdgeInsets.fromLTRB(12, 14, 12, 14),
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                child: Column(
                  children: [
                    ..._messages.expand(
                      (message) => [
                        _ChatBubble(message: message),
                        const SizedBox(height: 10),
                      ],
                    ),
                    if (!hasUserMessage)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (final question in _presetQuestions)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: _PresetQuestionButton(
                                text: question,
                                onTap: () => _sendPreset(question),
                              ),
                            ),
                        ],
                      ),
                    if (hasUserMessage)
                      _ChatRouteStatusCard(
                        loading: widget.routeLoading,
                        onTap: () => widget.onGo(ScreenStage.route),
                      ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .96),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: _border),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF8C3C14).withValues(alpha: .10),
                  blurRadius: 18,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      hintText: '输入你的规划需求…',
                      hintStyle: TextStyle(color: _inkSoft, fontSize: 13),
                    ),
                    style: const TextStyle(
                        color: _ink, fontWeight: FontWeight.w800, height: 1.35),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: widget.routeLoading ? null : _send,
                  child: Container(
                    width: 42,
                    height: 42,
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: _brown,
                      shape: BoxShape.circle,
                    ),
                    child: const Text('→',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w900)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatRouteStatusCard extends StatelessWidget {
  const _ChatRouteStatusCard({
    required this.loading,
    required this.onTap,
  });

  final bool loading;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(loading ? '⏳' : '✅', style: const TextStyle(fontSize: 24)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    loading ? '正在生成方案…' : '方案已生成，可查看今日路线',
                    style: const TextStyle(
                      color: _ink,
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              loading ? 'Agent 正在根据你的输入召回地点并生成真实路线。' : '路线已经准备好了，点下面按钮查看今日路线。',
              style: const TextStyle(
                color: _inkSoft,
                height: 1.4,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),
            _PrimaryButton(
              label: loading ? '正在生成方案…' : '查看今日路线 →',
              onTap: loading ? () {} : onTap,
            ),
          ],
        ),
      ),
    );
  }
}

class _PresetQuestionButton extends StatelessWidget {
  const _PresetQuestionButton({required this.text, required this.onTap});

  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _border),
        ),
        child: Row(
          children: [
            const Text('💬', style: TextStyle(fontSize: 16)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  color: _inkMid,
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const Text('›',
                style: TextStyle(
                    color: _inkSoft,
                    fontSize: 18,
                    fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }
}

class _ChatMessage {
  const _ChatMessage({required this.fromUser, required this.text});

  final bool fromUser;
  final String text;
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final _ChatMessage message;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment:
          message.fromUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 290),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: message.fromUser ? _brown : _card2,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: Radius.circular(message.fromUser ? 20 : 6),
            bottomRight: Radius.circular(message.fromUser ? 6 : 20),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: message.fromUser ? Colors.white : _inkMid,
            height: 1.45,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}

class _GuideScreen extends StatelessWidget {
  const _GuideScreen({
    required this.stops,
    required this.weather,
    required this.stopIndex,
    required this.visibleStopIndexes,
    required this.currentLat,
    required this.currentLng,
    required this.locationLoading,
    required this.locationError,
    required this.onGo,
    required this.onShowOverlay,
    required this.onNext,
    required this.onRefreshLocation,
    required this.onHeartbeatAdjust,
  });

  final List<_Stop> stops;
  final _WeatherSummary? weather;
  final int stopIndex;
  final List<int> visibleStopIndexes;
  final double? currentLat;
  final double? currentLng;
  final bool locationLoading;
  final String? locationError;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final VoidCallback onNext;
  final Future<void> Function() onRefreshLocation;
  final Future<void> Function({required String reason}) onHeartbeatAdjust;

  @override
  Widget build(BuildContext context) {
    final safeIndexes = visibleStopIndexes.isEmpty ? [0] : visibleStopIndexes;
    final currentPosition = stopIndex.clamp(0, safeIndexes.length - 1).toInt();
    final stop = stops[safeIndexes[currentPosition]];
    final next = currentPosition + 1 < safeIndexes.length
        ? stops[safeIndexes[currentPosition + 1]]
        : null;
    final remainingStops = [
      for (var i = currentPosition; i < safeIndexes.length; i++)
        stops[safeIndexes[i]],
    ];
    final distanceKm = _distanceKm(
      currentLat,
      currentLng,
      stop.lat,
      stop.lng,
    );
    final distanceLabel = distanceKm == null
        ? '位置待更新'
        : distanceKm < 1
            ? '${(distanceKm * 1000).round()}m'
            : '${distanceKm.toStringAsFixed(1)}km';
    final walkMinutes = distanceKm == null
        ? null
        : math.max(1, (distanceKm * 1000 / 75).round());
    final directionLabel = _directionLabel(
      currentLat,
      currentLng,
      stop.lat,
      stop.lng,
    );
    final locationStatus = locationLoading
        ? '正在尝试获取当前位置...'
        : currentLat != null && currentLng != null
            ? '已定位，可开始前往当前景点'
            : '暂未获取当前位置，仍可先查看下一站和路线方向';
    final refreshLocation = locationLoading ? () {} : () => onRefreshLocation();
    final queueMinutes = _queueMinutesFromStop(stop);
    final rainRisk = _hasRainRisk(weather);
    final heartbeatReason =
        queueMinutes >= 35 ? 'queue' : (rainRisk ? 'weather' : '');

    return Column(
      key: const ValueKey('guide'),
      children: [
        Expanded(
          flex: 7,
          child: Stack(
            children: [
              Positioned.fill(
                child: ClipRRect(
                  borderRadius: const BorderRadius.vertical(
                    bottom: Radius.circular(26),
                  ),
                  child: _RouteMap(
                    stops: remainingStops,
                    currentLat: currentLat,
                    currentLng: currentLng,
                  ),
                ),
              ),
              Positioned(
                  top: 18,
                  left: 16,
                  child: _TopBack(
                      label: '', onTap: () => onGo(ScreenStage.route))),
              Positioned(
                  top: 24,
                  right: 16,
                  child: _SoftPill(
                      label:
                          '导览中 ${currentPosition + 1}/${safeIndexes.length}')),
              Positioned(
                top: 74,
                right: 16,
                child: _SmallButton(
                  label: locationLoading ? '定位中...' : '刷新定位',
                  onTap: refreshLocation,
                ),
              ),
              Positioned(
                top: 74,
                left: 16,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .94),
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: .08),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Text(
                    '${stop.icon} ${stop.name}',
                    style: const TextStyle(
                      color: _ink,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ),
              Positioned(
                top: 122,
                left: 16,
                right: 16,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (weather != null || queueMinutes > 0)
                      _GuideStatusStrip(
                        weather: weather,
                        queueMinutes: queueMinutes,
                      ),
                    if (heartbeatReason.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      _HeartbeatBanner(
                        reason: heartbeatReason,
                        onAdjust: () =>
                            onHeartbeatAdjust(reason: heartbeatReason),
                      ),
                    ],
                  ],
                ),
              ),
              Positioned(
                  bottom: 24,
                  left: 24,
                  child: _SoftPill(
                      label: directionLabel ??
                          (next == null ? '已到最后一站' : next.transit))),
            ],
          ),
        ),
        Expanded(
          flex: 3,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: const BoxDecoration(
                color: _card,
                borderRadius: BorderRadius.vertical(top: Radius.circular(26))),
            child: LayoutBuilder(
              builder: (context, constraints) {
                return SingleChildScrollView(
                  child: ConstrainedBox(
                    constraints:
                        BoxConstraints(minHeight: constraints.maxHeight),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('当前目标',
                                style: TextStyle(
                                    color: _inkSoft,
                                    fontWeight: FontWeight.w800)),
                            Text(stop.name,
                                style: const TextStyle(
                                    fontSize: 22, fontWeight: FontWeight.w900)),
                            const SizedBox(height: 8),
                            _SoftPill(
                                label: walkMinutes == null
                                    ? locationStatus
                                    : '距当前景点 $distanceLabel · 步行约 $walkMinutes 分'),
                            const SizedBox(height: 8),
                            Text(
                              directionLabel == null
                                  ? locationStatus
                                  : '从你当前位置出发，$directionLabel 前往 ${stop.name}',
                              style: const TextStyle(
                                color: _inkMid,
                                height: 1.4,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            if (queueMinutes > 0) ...[
                              const SizedBox(height: 10),
                              _SoftPill(
                                label: queueMinutes >= 35
                                    ? '前方排队约 $queueMinutes 分钟 · 建议考虑替换'
                                    : '前方排队约 $queueMinutes 分钟',
                              ),
                            ],
                            if (rainRisk) ...[
                              const SizedBox(height: 8),
                              _SoftPill(
                                label: '2小时后可能有雨 · 建议提前出发或换室内点',
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                                child: _SmallButton(
                                    label: '怎么前往',
                                    onTap: () =>
                                        onShowOverlay(_AppOverlay.location))),
                            const SizedBox(width: 8),
                            Expanded(
                                child: _SmallButton(
                                    label: '心动提醒',
                                    onTap: () =>
                                        onShowOverlay(_AppOverlay.heart))),
                            const SizedBox(width: 8),
                            Expanded(
                                child: _SmallButton(
                                    label: '票根',
                                    onTap: () => onGo(ScreenStage.ticket))),
                          ],
                        ),
                        const SizedBox(height: 10),
                        _PrimaryButton(
                            label: next == null ? '完成并归档' : '✅ 已到达，前往下一站',
                            onTap: onNext),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

class _GuideStatusStrip extends StatelessWidget {
  const _GuideStatusStrip({
    required this.weather,
    required this.queueMinutes,
  });

  final _WeatherSummary? weather;
  final int queueMinutes;

  @override
  Widget build(BuildContext context) {
    final chips = <String>[
      if (weather != null)
        '天气 ${weather!.conditionLabel} ${weather!.temperatureLabel}',
      if ((weather?.rainLabel ?? '').isNotEmpty) '降雨 ${weather!.rainLabel}',
      if (queueMinutes > 0) '排队约 $queueMinutes 分钟',
    ];
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .95),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .08),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          for (final chip in chips) _SoftPill(label: chip),
        ],
      ),
    );
  }
}

class _HeartbeatBanner extends StatelessWidget {
  const _HeartbeatBanner({
    required this.reason,
    required this.onAdjust,
  });

  final String reason;
  final VoidCallback onAdjust;

  @override
  Widget build(BuildContext context) {
    final text = reason == 'queue'
        ? '前方排队约 45 分钟 · 发现更顺路的替代地点'
        : '2小时后可能下雨 · 建议优先改成室内路线';
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 12, 12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF1E6),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFF0B588)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFA05A32).withValues(alpha: .10),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        children: [
          const Text('💓', style: TextStyle(fontSize: 20)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: _ink,
                fontSize: 13,
                height: 1.35,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 10),
          _SmallButton(label: '换一下', onTap: onAdjust),
        ],
      ),
    );
  }
}

double? _distanceKm(double? lat1, double? lng1, double? lat2, double? lng2) {
  if (lat1 == null || lng1 == null || lat2 == null || lng2 == null) {
    return null;
  }
  final dLat = _guideDegToRad(lat2 - lat1);
  final dLng = _guideDegToRad(lng2 - lng1);
  final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
      math.cos(_guideDegToRad(lat1)) *
          math.cos(_guideDegToRad(lat2)) *
          math.sin(dLng / 2) *
          math.sin(dLng / 2);
  final c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
  return 6371 * c;
}

int _queueMinutesFromStop(_Stop stop) {
  final match = RegExp(r'排队\s*(\d+)').firstMatch(stop.note);
  return int.tryParse(match?.group(1) ?? '') ?? 0;
}

bool _hasRainRisk(_WeatherSummary? weather) {
  final condition = weather?.conditionLabel ?? '';
  if (condition.contains('雨') || condition.contains('雷')) return true;
  final rain = weather?.rainLabel ?? '';
  if (rain.isEmpty) return false;
  final match = RegExp(r'(\d+(?:\.\d+)?)').firstMatch(rain)?.group(1);
  final value = double.tryParse(match ?? '');
  return value != null && value > 0;
}

double _guideDegToRad(double degree) => degree * math.pi / 180;

String? _directionLabel(
    double? lat1, double? lng1, double? lat2, double? lng2) {
  if (lat1 == null || lng1 == null || lat2 == null || lng2 == null) {
    return null;
  }
  final y =
      math.sin(_guideDegToRad(lng2 - lng1)) * math.cos(_guideDegToRad(lat2));
  final x = math.cos(_guideDegToRad(lat1)) * math.sin(_guideDegToRad(lat2)) -
      math.sin(_guideDegToRad(lat1)) *
          math.cos(_guideDegToRad(lat2)) *
          math.cos(_guideDegToRad(lng2 - lng1));
  final bearing = (math.atan2(y, x) * 180 / math.pi + 360) % 360;
  final labels = ['正北', '东北', '正东', '东南', '正南', '西南', '正西', '西北'];
  final index = ((bearing + 22.5) / 45).floor() % labels.length;
  return '向${labels[index]}';
}
