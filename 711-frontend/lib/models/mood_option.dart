part of '../app_module.dart';

class _MoodOption {
  const _MoodOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.tags,
  });

  final String icon;
  final String title;
  final String subtitle;
  final List<String> tags;
}
