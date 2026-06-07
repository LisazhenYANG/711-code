part of '../../app_module.dart';

class _MoodCard extends StatelessWidget {
  const _MoodCard({
    required this.selected,
    required this.icon,
    required this.title,
    required this.sub,
    required this.tags,
    required this.onTap,
  });

  final bool selected;
  final String icon;
  final String title;
  final String sub;
  final List<String> tags;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedScale(
        scale: selected ? 1.03 : 1,
        duration: const Duration(milliseconds: 180),
        child: _ClayCard(
          color: selected ? const Color(0xFFFFFAF6) : _card,
          border: selected ? _brown : Colors.transparent,
          child: Stack(
            children: [
              if (selected)
                const Positioned(
                  top: 0,
                  right: 0,
                  child: CircleAvatar(
                    radius: 13,
                    backgroundColor: _brown,
                    child: Text('✓',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w900)),
                  ),
                ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: const BoxDecoration(
                        shape: BoxShape.circle, color: _card2),
                    alignment: Alignment.center,
                    child: Text(icon, style: const TextStyle(fontSize: 25)),
                  ),
                  const SizedBox(height: 10),
                  Text(title,
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w900)),
                  Text(sub,
                      style: const TextStyle(
                          color: _inkSoft,
                          fontSize: 12,
                          fontWeight: FontWeight.w700)),
                  const Spacer(),
                  Wrap(
                    spacing: 5,
                    runSpacing: 5,
                    children: tags.take(3).map((t) => _TinyTag(t)).toList(),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
