plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

android {
    namespace = "org.faro.tablet"
    compileSdk = 36

    defaultConfig {
        applicationId = "org.faro.tablet"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"

        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

chaquopy {
    defaultConfig {
        version = "3.12"
    }
}
