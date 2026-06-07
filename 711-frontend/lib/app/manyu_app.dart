part of '../app_module.dart';

class ManyuApp extends StatelessWidget {
  const ManyuApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: '慢游',
      scrollBehavior: const _ManyuScrollBehavior(),
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: _brown),
        scaffoldBackgroundColor: _bg,
        fontFamily: '.SF Pro Text',
        fontFamilyFallback: const [
          'SF Pro Text',
          '.SF Pro Display',
          'SF Pro Display',
          'PingFang SC',
          'Hiragino Sans GB',
          'Helvetica Neue',
          'Microsoft YaHei',
        ],
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: _ink, letterSpacing: 0),
        ),
      ),
      home: const Shell(),
    );
  }
}

class _ManyuScrollBehavior extends MaterialScrollBehavior {
  const _ManyuScrollBehavior();

  @override
  Set<PointerDeviceKind> get dragDevices => {
        PointerDeviceKind.touch,
        PointerDeviceKind.mouse,
        PointerDeviceKind.trackpad,
        PointerDeviceKind.stylus,
        PointerDeviceKind.unknown,
      };
}
