package com.example.loss.data;

import com.example.loss.BuildConfig;

public final class ImageUrls {

    private ImageUrls() {}

    /**
     * Превращает то, что лежит в БД/кэше/snapshot, в URL для Glide.
     * - file:///android_asset/... — snapshot, фото бандл в APK, отдаём как есть.
     * - Относительный /uploads/... — клеим к BASE_URL.
     * - Абсолютный с localhost/127.0.0.1 — переписываем на 10.0.2.2 (для эмулятора).
     * - Всё остальное (внешние https URL) — отдаём как есть.
     */
    public static String resolve(String url) {
        if (url == null || url.isEmpty()) return null;

        if (url.startsWith("file:///android_asset/")) return url;

        if (url.startsWith("/")) {
            String base = BuildConfig.BASE_URL;
            if (base.endsWith("/")) base = base.substring(0, base.length() - 1);
            return base + url;
        }

        if (url.contains("://127.0.0.1") || url.contains("://localhost")) {
            return url.replaceFirst("://(127\\.0\\.0\\.1|localhost)", "://10.0.2.2");
        }

        return url;
    }
}
