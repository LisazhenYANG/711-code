part of '../../app_module.dart';

class _AgentScreen extends StatelessWidget {
  const _AgentScreen({
    required this.stops,
    required this.routeOptions,
    required this.selectedRouteOptionIndex,
    required this.onGo,
    required this.onSelectRouteOption,
    required this.onConfirmSelectedRoute,
    required this.onShowOverlay,
  });

  final List<_Stop> stops;
  final List<_RouteOption> routeOptions;
  final int selectedRouteOptionIndex;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<int> onSelectRouteOption;
  final VoidCallback onConfirmSelectedRoute;
  final ValueChanged<_AppOverlay> onShowOverlay;

  @override
  Widget build(BuildContext context) {
    final hasOptions = routeOptions.isNotEmpty;
    final currentIndex = selectedRouteOptionIndex.clamp(
      0,
      hasOptions ? routeOptions.length - 1 : 0,
    );
    final currentOption = hasOptions ? routeOptions[currentIndex] : null;

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
            text: '我给你整理了 3 条路线。你可以按距离、评分和匹配度挑一条最想走的。',
          ),
          const SizedBox(height: 14),
          if (hasOptions) ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (var i = 0; i < routeOptions.length; i++) ...[
                    _StrategyChip(
                      label: routeOptions[i].label,
                      selected: i == currentIndex,
                      onTap: () => onSelectRouteOption(i),
                    ),
                    if (i < routeOptions.length - 1) const SizedBox(width: 8),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),
            _RoutePreviewCard(
              title: currentOption!.label,
              subtitle: currentOption.summary,
              metricLabel: currentOption.metricLabel,
              overloadHint: currentOption.overloadHint,
              selected: true,
              stops: currentOption.stops,
              confirmLabel: '确认这条路线 →',
              onConfirm: onConfirmSelectedRoute,
            ),
            const SizedBox(height: 12),
          ],
          _SmallButton(label: '自由聊聊', onTap: () => onGo(ScreenStage.freeChat)),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}

class _StrategyChip extends StatelessWidget {
  const _StrategyChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? _brown : Colors.white,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: selected ? _brown : _border),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFA05A32)
                  .withValues(alpha: selected ? .16 : .06),
              blurRadius: selected ? 16 : 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.white : _inkMid,
            fontSize: 13,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    );
  }
}
