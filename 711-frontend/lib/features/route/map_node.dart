part of '../../app_module.dart';

class _MapNode extends StatelessWidget {
  const _MapNode({required this.num, required this.icon, required this.color});

  final String num;
  final String icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 54,
      height: 54,
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
              color: color.withValues(alpha: .22),
              blurRadius: 12,
              offset: const Offset(0, 6))
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Text(icon, style: const TextStyle(fontSize: 23)),
          Positioned(
            right: 0,
            bottom: 0,
            child: CircleAvatar(
                radius: 11,
                backgroundColor: color,
                child: Text(num,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w900))),
          ),
        ],
      ),
    );
  }
}
