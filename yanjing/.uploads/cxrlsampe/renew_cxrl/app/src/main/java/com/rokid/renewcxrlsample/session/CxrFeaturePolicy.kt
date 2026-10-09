package com.rokid.renewcxrlsample.session

object CxrFeaturePolicy {
    fun allowedFeatures(sessionType: CxrSessionType): List<CxrFeature> = when (sessionType) {
        CxrSessionType.CUSTOM_VIEW -> listOf(CxrFeature.AUDIO, CxrFeature.PHOTO)
        CxrSessionType.CUSTOM_APP -> listOf(CxrFeature.AUDIO, CxrFeature.PHOTO, CxrFeature.CUSTOM_CMD)
    }

    fun isRouteAllowed(sessionType: CxrSessionType, route: String): Boolean =
        allowedFeatures(sessionType).any { it.route == route }

    fun isFeatureAllowed(sessionType: CxrSessionType, feature: CxrFeature): Boolean =
        feature in allowedFeatures(sessionType)
}
