part of '../../app_module.dart';

class _AgentScreen extends StatelessWidget {
  const _AgentScreen({
    required this.stops,
    required this.onGo,
    required this.onShowOverlay,
  });

  final List<_Stop> stops;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('agent'),
      child: Column(
        children: [
          Row(
            children: [
              _TopBack(label: '', onTap: () => onGo(ScreenStage.mood)),
              const SizedBox(width: 8),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('晚游 Agent',
                        style: TextStyle(
                            fontSize: 19, fontWeight: FontWeight.w900)),
                    Text('静安区 · 今天下午 · 2人',
                        style: TextStyle(color: _inkSoft, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          const _AgentBubble(
            text: '好的！根据你的偏好，帮你搭了一条静安的下午线——3站，步行 + 地铁串联，慢悠悠刚刚好 ☕',
          ),
          const SizedBox(height: 14),
          _RoutePreviewCard(
            stops: stops,
            onConfirm: () => onGo(ScreenStage.route),
          ),
          const SizedBox(height: 12),
          _SmallButton(label: '自由聊聊', onTap: () => onGo(ScreenStage.freeChat)),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}
