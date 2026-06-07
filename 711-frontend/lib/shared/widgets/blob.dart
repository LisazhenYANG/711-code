part of '../../app_module.dart';

class _Blob extends StatelessWidget {
  const _Blob(
      {this.top,
      this.left,
      this.right,
      this.bottom,
      required this.color,
      required this.size});

  final double? top;
  final double? left;
  final double? right;
  final double? bottom;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      top: top,
      left: left,
      right: right,
      bottom: bottom,
      child: Transform.rotate(
        angle: math.pi / 9,
        child: Container(
          width: size,
          height: size * .78,
          decoration: BoxDecoration(
            color: color.withValues(alpha: .56),
            borderRadius: BorderRadius.circular(size),
          ),
        ),
      ),
    );
  }
}
