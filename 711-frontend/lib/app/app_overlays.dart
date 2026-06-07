part of '../app_module.dart';

class _AppOverlays extends StatelessWidget {
  const _AppOverlays({
    required this.state,
    required this.onGo,
    required this.onShowOverlay,
    required this.onClose,
    required this.onRestoreStops,
    required this.onRouteAction,
    required this.onCompleteBooking,
    required this.onLoadMealRestaurants,
    required this.onLoadAddPlaceRecommendations,
  });

  final _AppState state;
  final ValueChanged<ScreenStage> onGo;
  final ValueChanged<_AppOverlay> onShowOverlay;
  final VoidCallback onClose;
  final VoidCallback onRestoreStops;
  final Future<void> Function(String action,
      {int? index,
      String value,
      int? recommendationIndex,
      List<String> priorities}) onRouteAction;
  final Future<void> Function() onCompleteBooking;
  final Future<List<_MealRestaurant>> Function(String slot) onLoadMealRestaurants;
  final Future<List<_RecommendationItem>> Function() onLoadAddPlaceRecommendations;

  @override
  Widget build(BuildContext context) {
    if (state.overlay == _AppOverlay.none) return const SizedBox.shrink();
    final visibleIndexes =
        state.visibleStopIndexes.isEmpty ? [0] : state.visibleStopIndexes;
    final overlayStop = state.routeStops[visibleIndexes[
        state.guideStopIndex.clamp(0, visibleIndexes.length - 1).toInt()]];

    final content = switch (state.overlay) {
      _AppOverlay.plus => _PlusSheet(onGo: onGo, onClose: onClose),
      _AppOverlay.venue => _VenueSheet(
          recommendations: state.recommendations,
          onClose: onClose,
          onShowOverlay: onShowOverlay),
      _AppOverlay.venueDetail => _VenueDetailSheet(
          recommendation: state.recommendations.isEmpty
              ? null
              : state.recommendations[state.selectedRecommendationIndex
                  .clamp(0, state.recommendations.length - 1)
                  .toInt()],
          onClose: onClose,
        ),
      _AppOverlay.addPlace => _AddPlaceSheet(
          loadRecommendations: onLoadAddPlaceRecommendations,
          onAdd: (name) {
            onRouteAction('add_place', value: name);
          },
          onAddCustom: (name) {
            onRouteAction('add_place', value: name);
          },
          onClose: onClose,
        ),
      _AppOverlay.meal => _MealSheet(
          loadRestaurants: onLoadMealRestaurants,
          onAddMeal: (slot) {
            onRouteAction('add_meal', value: slot);
          },
          onClose: onClose,
        ),
      _AppOverlay.transit => _TransitSheet(
          onSelect: (mode) {
            onRouteAction('transit',
                index: state.selectedStopIndex, value: mode);
          },
          onClose: onClose,
        ),
      _AppOverlay.spot => _SpotSheet(
          stop: state.routeStops[state.selectedStopIndex
              .clamp(0, state.routeStops.length - 1)
              .toInt()],
          onClose: onClose,
        ),
      _AppOverlay.recDetail => _RecDetailSheet(
          recommendation: state.recommendations.isEmpty
              ? null
              : state.recommendations[state.selectedRecommendationIndex
                  .clamp(0, state.recommendations.length - 1)
                  .toInt()],
          onClose: onClose,
        ),
      _AppOverlay.lockInfo =>
        _LockInfoSheet(onClose: onClose, onRestoreStops: onRestoreStops),
      _AppOverlay.payment => _PaymentSheet(
          bookings: state.selectedBookingIndexes.isEmpty
              ? const []
              : [
                  for (var i = 0; i < state.bookings.length; i++)
                    if (state.selectedBookingIndexes.contains(i))
                      state.bookings[i],
                ],
          onClose: onClose,
          onComplete: onCompleteBooking,
        ),
      _AppOverlay.location => _LocationSheet(
          stop: overlayStop,
          currentLat: state.currentLat,
          currentLng: state.currentLng,
          onClose: onClose,
        ),
      _AppOverlay.heart => _HeartSheet(
          onChoose: (value) {
            onRouteAction('heart', value: value);
          },
          onClose: onClose,
        ),
      _AppOverlay.none => const SizedBox.shrink(),
    };

    return Positioned.fill(
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onClose,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
          color: Colors.black.withValues(alpha: .34),
          child: SafeArea(
            top: false,
            child: Align(
              alignment: Alignment.bottomCenter,
              child: GestureDetector(
                onTap: () {},
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 1, end: 0),
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) {
                    return Transform.translate(
                      offset: Offset(0, 48 * value),
                      child: Opacity(
                        opacity: 1 - (value * 0.08),
                        child: child,
                      ),
                    );
                  },
                  child: content,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
