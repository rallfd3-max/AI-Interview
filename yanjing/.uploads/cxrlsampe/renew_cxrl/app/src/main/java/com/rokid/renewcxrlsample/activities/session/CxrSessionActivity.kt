package com.rokid.renewcxrlsample.activities.session

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.rokid.renewcxrlsample.R
import com.rokid.renewcxrlsample.activities.audio.AudioUsageViewModel
import com.rokid.renewcxrlsample.activities.customCMD.CustomCmdViewModel
import com.rokid.renewcxrlsample.activities.photo.PhotoUsageViewModel
import com.rokid.renewcxrlsample.app.CONSTANT
import com.rokid.renewcxrlsample.navigation.observeCxrSceneNavigation
import com.rokid.renewcxrlsample.session.CxrFeature
import com.rokid.renewcxrlsample.session.CxrFeaturePolicy
import com.rokid.renewcxrlsample.session.CxrSessionType
import com.rokid.renewcxrlsample.session.SceneRoutes
import com.rokid.renewcxrlsample.ui.feature.AudioUsageScreen
import com.rokid.renewcxrlsample.ui.feature.CustomCmdScreen
import com.rokid.renewcxrlsample.ui.feature.PhotoUsageScreen
import com.rokid.renewcxrlsample.ui.theme.RenewCXRLSampleTheme

class CxrSessionActivity : ComponentActivity() {

    companion object {
        private const val TAG = "CxrSessionActivity"
    }

    private val hubViewModel by viewModels<SessionHubViewModel>()
    private val audioViewModel by viewModels<AudioUsageViewModel>()
    private val photoViewModel by viewModels<PhotoUsageViewModel>()
    private val cmdViewModel by viewModels<CustomCmdViewModel>()

    private val mediaPermissionRequestLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            Log.i(TAG, "[GlassApp] READ_EXTERNAL_STORAGE result: granted=$granted")
            if (granted) hubViewModel.installApp()
        }

    private val allFilesAccessPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            val hasAllFiles = hasManageAllFilesAccessPermission()
            Log.i(TAG, "[GlassApp] MANAGE_ALL_FILES_ACCESS result: granted=$hasAllFiles")
            if (hasAllFiles) {
                if (needRequestReadExternalStoragePermission()) {
                    mediaPermissionRequestLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
                } else {
                    hubViewModel.installApp()
                }
            }
        }

    private val shareAudioLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {}

    private lateinit var sessionType: CxrSessionType
    private var sessionToken: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        sessionType = CxrSessionType.fromIntentExtra(intent.getStringExtra(CONSTANT.EXTRA_SESSION_TYPE))
        sessionToken = intent.getStringExtra(CONSTANT.EXTRA_TOKEN)
        Log.i(
            TAG,
            "[GlassApp] onCreate: sessionType=$sessionType tokenPresent=${!sessionToken.isNullOrBlank()}"
        )
        hubViewModel.init(this, sessionToken, sessionType)
        observeCxrSceneNavigation { sessionToken }

        setContent {
            RenewCXRLSampleTheme {
                val navController = rememberNavController()
                val activity = this@CxrSessionActivity
                NavHost(
                    navController = navController,
                    startDestination = SceneRoutes.HUB
                ) {
                    composable(SceneRoutes.HUB) {
                        SessionHubScreen(
                            viewModel = hubViewModel,
                            sessionType = sessionType,
                            onNavigateToFeature = { feature ->
                                if (CxrFeaturePolicy.isFeatureAllowed(sessionType, feature)) {
                                    navController.navigate(feature.route)
                                }
                            },
                            onRequestInstall = { activity.requestInstallPermissions() }
                        )
                    }
                    composable(SceneRoutes.AUDIO) {
                        FeatureRoute(
                            sessionType = sessionType,
                            onInit = {
                                audioViewModel.init(activity, sessionToken, sessionType)
                            },
                            onRelease = { audioViewModel.release() }
                        ) {
                            AudioUsageScreen(
                                viewModel = audioViewModel,
                                sessionType = sessionType,
                                onBack = { navController.popBackStack() },
                                onShareAudio = {
                                    audioViewModel.buildShareIntent(activity)?.let { shareIntent ->
                                        shareAudioLauncher.launch(
                                            Intent.createChooser(
                                                shareIntent,
                                                getString(R.string.audio_share_title)
                                            )
                                        )
                                    }
                                }
                            )
                        }
                    }
                    composable(SceneRoutes.PHOTO) {
                        FeatureRoute(
                            sessionType = sessionType,
                            onInit = {
                                photoViewModel.init(activity, sessionToken, sessionType)
                            },
                            onRelease = { photoViewModel.release() }
                        ) {
                            PhotoUsageScreen(
                                viewModel = photoViewModel,
                                sessionType = sessionType,
                                onBack = { navController.popBackStack() }
                            )
                        }
                    }
                    composable(SceneRoutes.CMD) {
                        if (!CxrFeaturePolicy.isRouteAllowed(sessionType, SceneRoutes.CMD)) {
                            LaunchedEffect(Unit) { navController.popBackStack() }
                        } else {
                            FeatureRoute(
                                sessionType = sessionType,
                                onInit = {
                                    cmdViewModel.init(activity, sessionToken, sessionType)
                                },
                                onRelease = { cmdViewModel.release() }
                            ) {
                                CustomCmdScreen(
                                    viewModel = cmdViewModel,
                                    sessionType = sessionType,
                                    onBack = { navController.popBackStack() }
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        if (isFinishing) {
            hubViewModel.release()
        }
        super.onDestroy()
    }

    private fun requestInstallPermissions() {
        val needAllFiles = needRequestManageAllFilesAccessPermission()
        val needRead = needRequestReadExternalStoragePermission()
        Log.i(
            TAG,
            "[GlassApp] requestInstallPermissions: needAllFiles=$needAllFiles needRead=$needRead"
        )
        if (needAllFiles) {
            requestManageAllFilesAccessPermission()
        } else if (needRead) {
            mediaPermissionRequestLauncher.launch(Manifest.permission.READ_EXTERNAL_STORAGE)
        } else {
            hubViewModel.installApp()
        }
    }

    private fun needRequestReadExternalStoragePermission(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) return false
        return checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED
    }

    private fun needRequestManageAllFilesAccessPermission(): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return false
        return !hasManageAllFilesAccessPermission()
    }

    private fun hasManageAllFilesAccessPermission(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.R || Environment.isExternalStorageManager()
    }

    private fun requestManageAllFilesAccessPermission() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return
        val intent = Intent(
            Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
            Uri.parse("package:$packageName")
        )
        allFilesAccessPermissionLauncher.launch(intent)
    }
}

@androidx.compose.runtime.Composable
private fun FeatureRoute(
    sessionType: CxrSessionType,
    onInit: () -> Unit,
    onRelease: () -> Unit,
    content: @androidx.compose.runtime.Composable () -> Unit
) {
    DisposableEffect(sessionType) {
        onInit()
        onDispose { onRelease() }
    }
    content()
}
