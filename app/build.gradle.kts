plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val appVersionName = "1.0.8"

android {
    namespace = "com.quark.watermark"
    compileSdk = 34

    setProperty("archivesBaseName", "夸克去水印_v${appVersionName}")

    defaultConfig {
        applicationId = "com.quark.watermark"
        minSdk = 26
        targetSdk = 34
        versionCode = 9
        versionName = appVersionName
    }

    signingConfigs {
        create("release") {
            storeFile = file("../quark-watermark.keystore")
            storePassword = "123456"
            keyAlias = "quark"
            keyPassword = "123456"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }

    buildFeatures {
        compose = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.5"
    }
}

dependencies {
    // iText 7
    implementation("com.itextpdf:itext7-core:7.2.5")

    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.activity:activity-compose:1.8.1")
    debugImplementation("androidx.compose.ui:ui-tooling")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // Unit test
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
}
