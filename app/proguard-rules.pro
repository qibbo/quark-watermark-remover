# Add project specific ProGuard rules here.
-keep class com.itextpdf.** { *; }

# iText 7 依赖的 jackson 库
-keep class com.fasterxml.jackson.** { *; }
-dontwarn com.fasterxml.jackson.**

# iText 7 使用的 java.awt（Android 上不存在，但代码中有引用）
-dontwarn java.awt.**
-dontwarn javax.imageio.**

# SLF4J
-dontwarn org.slf4j.**
