part of '../../app_module.dart';

class _ClayCard extends StatelessWidget {
  const _ClayCard({
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.color = _card,
    this.border,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color color;
  final Color? border;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: border ?? Colors.transparent, width: 2),
        boxShadow: [
          BoxShadow(
              color: Colors.white.withValues(alpha: .95),
              blurRadius: 2,
              offset: const Offset(0, -1)),
          BoxShadow(
              color: const Color(0xFFA05A32).withValues(alpha: .12),
              blurRadius: 22,
              offset: const Offset(0, 8)),
          BoxShadow(
              color: const Color(0xFFA05A32).withValues(alpha: .06),
              blurRadius: 8,
              offset: const Offset(0, 3)),
        ],
      ),
      child: child,
    );
  }
}
