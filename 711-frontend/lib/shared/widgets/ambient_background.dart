part of '../../app_module.dart';

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        _Blob(top: -80, left: -60, color: const Color(0xFFFFC9BE), size: 210),
        _Blob(top: 20, right: -70, color: const Color(0xFFE4D7FF), size: 190),
        _Blob(bottom: 60, left: -80, color: const Color(0xFFDDF3E7), size: 220),
        _Blob(
            bottom: -70, right: -60, color: const Color(0xFFFFE1A9), size: 190),
        const Positioned(
            top: 80,
            left: 40,
            child: Text('☁️', style: TextStyle(fontSize: 32))),
        const Positioned(
            top: 150,
            right: 70,
            child: Text('✨', style: TextStyle(fontSize: 28))),
        const Positioned(
            bottom: 115,
            left: 70,
            child: Text('⭐', style: TextStyle(fontSize: 26))),
      ],
    );
  }
}
