part of '../../app_module.dart';

class _RouteScreen extends StatelessWidget {
  const _RouteScreen({
    required this.stops,
    required this.lockedStops,
    required this.visibleStopIndexes,
    required this.chatOpen,
    required this.onGo,
    required this.onToggleLock,
    required this.onDeleteStop,
    required this.onShowOverlay,
    required this.onShowStopDetail,
    required this.onShowTransitForStop,
    required this.onToggleChat,
    required this.onChatCommand,
    required this.onApplySuggestedRoute,
  });

  final List<_Stop> stops;
  final Set<int> lockedStops;
  final List<int> visibleStopIndexes;
  final bool chatOpen;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<int> onToggleLock;
  final ValueChanged<int> onDeleteStop;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final ValueChanged<int> onShowStopDetail;
  final ValueChanged<int> onShowTransitForStop;
  final VoidCallback onToggleChat;
  final Stream<_ChatStreamEvent> Function(String message) onChatCommand;
  final ValueChanged<List<_Stop>> onApplySuggestedRoute;

  @override
  Widget build(BuildContext context) {
    if (chatOpen) {
      return _RouteChatFullscreen(
        onBack: onToggleChat,
        onSend: onChatCommand,
        onApplySuggestedRoute: onApplySuggestedRoute,
      );
    }

    return _ScreenScroll(
      key: const ValueKey('route'),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 118),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _TopBack(label: '', onTap: () => onGo(ScreenStage.home)),
              const SizedBox(width: 8),
              Expanded(
                child: Text('今日路线 · ${visibleStopIndexes.length} 站',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w900)),
              ),
              _SmallButton(
                  label: '完成规划', onTap: () => onGo(ScreenStage.execute)),
            ],
          ),
          const SizedBox(height: 12),
          _ClayCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                const SizedBox(height: 8),
                SizedBox(
                    height: 244,
                    child: _RouteMap(stops: [
                      for (final index in visibleStopIndexes) stops[index],
                    ])),
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                  child: Row(
                    children: [
                      const _SoftPill(label: '🚶 步行 1.3km'),
                      const SizedBox(width: 8),
                      const _SoftPill(label: '⏱ 2.5h'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          ...List.generate(visibleStopIndexes.length, (position) {
            final i = visibleStopIndexes[position];
            final stop = stops[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _StopCard(
                index: position,
                stop: stop,
                locked: lockedStops.contains(i),
                onTap: () => onShowStopDetail(i),
                onLock: () => onToggleLock(i),
                onDelete: () => onDeleteStop(i),
                onTransit: () => onShowTransitForStop(i),
              ),
            );
          }),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _RouteDockButton(
                  label: '🍽️ 安排吃饭',
                  onTap: () => onShowOverlay(_AppOverlay.meal),
                ),
              ),
              const SizedBox(width: 8),
              _RouteCircleButton(
                label: '＋',
                onTap: () => onShowOverlay(_AppOverlay.addPlace),
              ),
              const SizedBox(width: 8),
              _RouteCircleButton(
                label: '💬',
                onTap: onToggleChat,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RouteChatFullscreen extends StatelessWidget {
  const _RouteChatFullscreen({
    required this.onBack,
    required this.onSend,
    required this.onApplySuggestedRoute,
  });

  final VoidCallback onBack;
  final Stream<_ChatStreamEvent> Function(String message) onSend;
  final ValueChanged<List<_Stop>> onApplySuggestedRoute;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Column(
        children: [
          Row(
            children: [
              _TopBack(label: '', onTap: onBack),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  '路线助手',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _RouteChatPanel(
              onBack: onBack,
              onSend: onSend,
              onApplySuggestedRoute: onApplySuggestedRoute,
              fullscreen: true,
            ),
          ),
        ],
      ),
    );
  }
}

class _RouteDockButton extends StatelessWidget {
  const _RouteDockButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 46,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(23),
          border: Border.all(color: _border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF8C3C14).withValues(alpha: .08),
              blurRadius: 14,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: _inkMid,
            fontSize: 12,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}

class _RouteCircleButton extends StatelessWidget {
  const _RouteCircleButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 46,
        height: 46,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: label == '＋' ? _brown : Colors.white,
          shape: BoxShape.circle,
          border: Border.all(color: label == '＋' ? _brown : _border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF8C3C14).withValues(alpha: .12),
              blurRadius: 14,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Text(
          label,
          style: TextStyle(
            color: label == '＋' ? Colors.white : _inkMid,
            fontSize: label == '＋' ? 25 : 20,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}

class _RouteChatPanel extends StatefulWidget {
  const _RouteChatPanel({
    required this.onBack,
    required this.onSend,
    required this.onApplySuggestedRoute,
    this.fullscreen = false,
  });

  final VoidCallback onBack;
  final Stream<_ChatStreamEvent> Function(String message) onSend;
  final ValueChanged<List<_Stop>> onApplySuggestedRoute;
  final bool fullscreen;

  @override
  State<_RouteChatPanel> createState() => _RouteChatPanelState();
}

class _RouteChatPanelState extends State<_RouteChatPanel> {
  final controller = TextEditingController();
  final messages = <_RouteChatMessage>[
    const _RouteChatMessage(
      text: '我在。你可以直接说：推荐一个地点、加武康路、安排晚饭、少走一点、删除第二站、锁定第一站。',
      fromUser: false,
    ),
  ];
  bool sending = false;

  static const presets = [
    '推荐一个咖啡',
    '加武康路',
    '安排晚饭',
    '少走一点',
    '删除第二站',
    '锁定第一站',
  ];

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _ClayCard(
      padding: widget.fullscreen
          ? const EdgeInsets.fromLTRB(16, 16, 16, 12)
          : const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!widget.fullscreen) ...[
            _TopBack(label: '返回行程', onTap: widget.onBack),
            const SizedBox(height: 14),
          ],
          Expanded(
            child: ListView.separated(
              padding: EdgeInsets.zero,
              itemBuilder: (context, index) => _RouteChatBubble(
                message: messages[index],
                onApply: () {
                  final pending = messages[index].pendingRoute;
                  if (pending.isEmpty) return;
                  widget.onApplySuggestedRoute(pending);
                  setState(() {
                    messages[index] = messages[index].copyWith(
                      text: '已加入路线。你也可以继续告诉我想怎么调整。',
                      recommendations: const [],
                      pendingRoute: const [],
                      showActions: false,
                    );
                  });
                },
                onDismiss: () {
                  setState(() {
                    messages[index] = messages[index].copyWith(
                      text: '这几个点我先记着，不加入当前路线。你也可以继续问我别的推荐。',
                      showActions: false,
                    );
                  });
                },
              ),
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemCount: messages.length,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final preset in presets)
                GestureDetector(
                  onTap: sending ? null : () => _send(preset),
                  child: _TinyTag(preset),
                ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  enabled: !sending,
                  minLines: 1,
                  maxLines: 3,
                  textInputAction: TextInputAction.send,
                  decoration: InputDecoration(
                    hintText: '告诉晚晚怎么调整路线…',
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 11),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: _border),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: _border),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(color: _brown, width: 1.4),
                    ),
                  ),
                  onSubmitted: (_) => _send(controller.text),
                ),
              ),
              const SizedBox(width: 8),
              _SmallButton(
                label: sending ? '处理中' : '发送',
                onTap: sending ? () {} : () => _send(controller.text),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _send(String raw) async {
    final text = raw.trim();
    if (text.isEmpty || sending) return;
    setState(() {
      sending = true;
      messages.add(_RouteChatMessage(text: text, fromUser: true));
      messages.add(const _RouteChatMessage(text: '正在思考…', fromUser: false));
      controller.clear();
    });
    try {
      await for (final event in widget.onSend(text)) {
        if (!mounted) return;
        setState(() {
          messages[messages.length - 1] = _RouteChatMessage(
            text: event.message,
            fromUser: false,
            recommendations: event.recommendations,
            pendingRoute: event.intent == 'recommend_place'
                ? event.updatedStops
                : const [],
            showActions: event.intent == 'recommend_place' &&
                event.updatedStops.isNotEmpty,
          );
          if (event.done) {
            sending = false;
          }
        });
      }
      if (!mounted) return;
      setState(() {
        sending = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        messages[messages.length - 1] = const _RouteChatMessage(
            text: '刚才没能连上路线服务。确认 backend 开着后再试一次。',
            fromUser: false);
        sending = false;
      });
    }
  }
}

class _RouteChatMessage {
  const _RouteChatMessage({
    required this.text,
    required this.fromUser,
    this.recommendations = const [],
    this.pendingRoute = const [],
    this.showActions = false,
  });

  final String text;
  final bool fromUser;
  final List<_RecommendationItem> recommendations;
  final List<_Stop> pendingRoute;
  final bool showActions;

  _RouteChatMessage copyWith({
    String? text,
    bool? fromUser,
    List<_RecommendationItem>? recommendations,
    List<_Stop>? pendingRoute,
    bool? showActions,
  }) {
    return _RouteChatMessage(
      text: text ?? this.text,
      fromUser: fromUser ?? this.fromUser,
      recommendations: recommendations ?? this.recommendations,
      pendingRoute: pendingRoute ?? this.pendingRoute,
      showActions: showActions ?? this.showActions,
    );
  }
}

class _RouteChatBubble extends StatelessWidget {
  const _RouteChatBubble({
    required this.message,
    required this.onApply,
    required this.onDismiss,
  });

  final _RouteChatMessage message;
  final VoidCallback onApply;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.fromUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 292),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: message.fromUser ? _brown : _card2,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(message.fromUser ? 18 : 5),
            bottomRight: Radius.circular(message.fromUser ? 5 : 18),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: message.fromUser ? Colors.white : _inkMid,
                height: 1.38,
                fontWeight: FontWeight.w800,
              ),
            ),
            if (!message.fromUser && message.recommendations.isNotEmpty) ...[
              const SizedBox(height: 10),
              for (final item in message.recommendations.take(3))
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: GestureDetector(
                    onTap: message.showActions ? onApply : null,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: message.showActions ? _brown : _border,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF8C3C14).withValues(alpha: .08),
                            blurRadius: 10,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text('${item.icon} ${item.title}',
                                    style: const TextStyle(
                                        color: _ink,
                                        fontWeight: FontWeight.w900)),
                              ),
                              if (message.showActions)
                                const Text(
                                  '点击加入',
                                  style: TextStyle(
                                    color: _brown,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(item.subtitle,
                              style: const TextStyle(
                                  color: _inkSoft,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
            if (!message.fromUser && message.showActions) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  Expanded(
                    child: _SmallButton(label: '加入路线', onTap: onApply),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _SmallButton(label: '暂不加入', onTap: onDismiss),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
