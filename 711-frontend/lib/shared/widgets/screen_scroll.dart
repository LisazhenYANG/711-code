part of '../../app_module.dart';

class _ScreenScroll extends StatelessWidget {
  const _ScreenScroll(
      {super.key,
      required this.child,
      this.padding = const EdgeInsets.fromLTRB(16, 14, 16, 118)});

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: padding,
      physics: const BouncingScrollPhysics(),
      child: child,
    );
  }
}
