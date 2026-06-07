part of '../../app_module.dart';

class _BottomTabs extends StatelessWidget {
  const _BottomTabs(
      {required this.selected, required this.onTap, required this.compact});

  final int selected;
  final ValueChanged<int> onTap;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      ignoring: false,
      child: Container(
        width: compact ? MediaQuery.sizeOf(context).width - 28 : 360,
        margin: const EdgeInsets.only(bottom: 18),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: .94),
          borderRadius: BorderRadius.circular(32),
          boxShadow: [
            BoxShadow(
                color: const Color(0xFF8C3C14).withValues(alpha: .14),
                blurRadius: 24,
                offset: const Offset(0, 10)),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _TabItem(
                icon: '🏠',
                label: '首页',
                active: selected == 0,
                onTap: () => onTap(0)),
            _TabItem(
                icon: '+',
                label: '规划',
                active: selected == 1,
                center: true,
                onTap: () => onTap(1)),
            _TabItem(
                icon: '👤',
                label: '我的',
                active: selected == 2,
                onTap: () => onTap(2)),
          ],
        ),
      ),
    );
  }
}

class _TabItem extends StatelessWidget {
  const _TabItem(
      {required this.icon,
      required this.label,
      required this.active,
      required this.onTap,
      this.center = false});

  final String icon;
  final String label;
  final bool active;
  final bool center;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: center ? 64 : 82,
        height: center ? 54 : 50,
        decoration: BoxDecoration(
          color: center ? _brown : (active ? _card2 : Colors.transparent),
          borderRadius: BorderRadius.circular(26),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(icon,
                style: TextStyle(
                    fontSize: center ? 26 : 19,
                    color: center ? Colors.white : _ink)),
            if (!center)
              Text(label,
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w900,
                      color: active ? _brown : _inkSoft)),
          ],
        ),
      ),
    );
  }
}
