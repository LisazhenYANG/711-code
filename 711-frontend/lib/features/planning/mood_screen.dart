part of '../../app_module.dart';

class _MoodScreen extends StatelessWidget {
  const _MoodScreen({
    required this.selected,
    required this.loading,
    required this.loadingMessage,
    required this.onMood,
    required this.onGo,
    required this.onGenerateRoute,
  });

  final Set<int> selected;
  final bool loading;
  final String loadingMessage;
  final ValueChanged<int> onMood;
  final ValueChanged<ScreenStage> onGo;
  final Future<void> Function({String freeText}) onGenerateRoute;

  @override
  Widget build(BuildContext context) {
    return _ScreenScroll(
      key: const ValueKey('mood'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TopBack(label: '返回', onTap: () => onGo(ScreenStage.home)),
          const SizedBox(height: 12),
          _SoftPill(
              label: '● ${selected.length} 种基调 · 多选均可',
              color: const Color(0xFFFFE9DF)),
          const SizedBox(height: 12),
          const Text('今天，想干点什么？',
              style: TextStyle(
                  fontSize: 28, fontWeight: FontWeight.w900, color: _ink)),
          const SizedBox(height: 4),
          const Text('选一选，搭配今天的心情',
              style: TextStyle(color: _inkMid, fontWeight: FontWeight.w700)),
          const SizedBox(height: 18),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _moodOptions.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: .88,
            ),
            itemBuilder: (context, i) {
              final mood = _moodOptions[i];
              return _MoodCard(
                selected: selected.contains(i),
                icon: mood.icon,
                title: mood.title,
                sub: mood.subtitle,
                tags: mood.tags,
                onTap: () => onMood(i),
              );
            },
          ),
          const SizedBox(height: 18),
          if (loading) ...[
            _ClayCard(
              child: Row(
                children: [
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2.4),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      loadingMessage.isEmpty ? '正在生成路线…' : loadingMessage,
                      style: const TextStyle(
                        color: _inkMid,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
          ],
          _PrimaryButton(
            label: loading ? '正在生成路线…' : '生成今日路线 →',
            onTap: loading ? () {} : () => onGenerateRoute(),
          ),
          const SizedBox(height: 100),
        ],
      ),
    );
  }
}
