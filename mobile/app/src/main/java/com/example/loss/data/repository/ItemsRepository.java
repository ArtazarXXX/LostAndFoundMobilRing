package com.example.loss.data.repository;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.util.Log;

import com.example.loss.data.api.ApiClient;
import com.example.loss.data.api.ApiService;
import com.example.loss.data.model.ClaimRequest;
import com.example.loss.data.model.Item;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Response;

public class ItemsRepository {

    public interface Callback<T> {
        void onResult(T value, boolean offline);
        void onError(Throwable error);
    }

    private static final String TAG = "ItemsRepository";
    private static final String SEED_FILE = "seed_items.json";
    private static final String CACHE_FILE = "items_cache.json";

    private final Context appContext;
    private final ApiService api;
    private final Gson gson = new Gson();
    private final ExecutorService io = Executors.newSingleThreadExecutor();

    public ItemsRepository(Context context) {
        this.appContext = context.getApplicationContext();
        this.api = ApiClient.get();
    }

    public void listAccepted(Callback<List<Item>> cb) {
        listAccepted(null, null, cb);
    }

    public void listAccepted(String type, String category, Callback<List<Item>> cb) {
        io.execute(() -> {
            try {
                Response<List<Item>> resp = api.listAccepted(type, category).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    writeCache(resp.body());
                    cb.onResult(resp.body(), false);
                    return;
                }
                Log.w(TAG, "listAccepted HTTP " + resp.code() + ", fallback to local");
            } catch (IOException e) {
                Log.w(TAG, "listAccepted network error, fallback to local: " + e.getMessage());
            } catch (Exception e) {
                cb.onError(e);
                return;
            }
            // Offline filter
            List<Item> local = loadLocal();
            java.util.List<Item> filtered = new java.util.ArrayList<>();
            for (Item it : local) {
                boolean matchType = (type == null || type.isEmpty() || type.equalsIgnoreCase(it.type));
                boolean matchCat = (category == null || category.isEmpty() || "all".equalsIgnoreCase(category) || category.equalsIgnoreCase(it.category));
                if (matchType && matchCat) {
                    filtered.add(it);
                }
            }
            cb.onResult(filtered, true);
        });
    }

    public void getItem(int id, Callback<Item> cb) {
        io.execute(() -> {
            try {
                Response<Item> resp = api.getItem(id).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    cb.onResult(resp.body(), false);
                    return;
                }
            } catch (IOException e) {
                Log.w(TAG, "getItem network error, fallback to local: " + e.getMessage());
            } catch (Exception e) {
                cb.onError(e);
                return;
            }
            for (Item it : loadLocal()) {
                if (it.id == id) {
                    cb.onResult(it, true);
                    return;
                }
            }
            cb.onError(new IllegalStateException("Предмет не найден в оффлайн-данных"));
        });
    }

    public void submitItem(Uri photoUri, String place, String comment, Callback<Item> cb) {
        submitItem(photoUri, place, comment, "found", "other", cb);
    }

    public void submitItem(Uri photoUri, String place, String comment, String type, String category, Callback<Item> cb) {
        io.execute(() -> {
            try {
                byte[] bytes = compressImage(photoUri, 1600, 85);

                MultipartBody.Part part = MultipartBody.Part.createFormData(
                        "photo", "upload.jpg",
                        RequestBody.create(MediaType.parse("image/jpeg"), bytes));
                RequestBody placeBody = RequestBody.create(
                        MediaType.parse("text/plain; charset=utf-8"), place);
                RequestBody commentBody = RequestBody.create(
                        MediaType.parse("text/plain; charset=utf-8"), comment);
                RequestBody typeBody = RequestBody.create(
                        MediaType.parse("text/plain; charset=utf-8"), type != null ? type : "found");
                RequestBody catBody = RequestBody.create(
                        MediaType.parse("text/plain; charset=utf-8"), category != null ? category : "other");
                RequestBody authorBody = RequestBody.create(
                        MediaType.parse("text/plain; charset=utf-8"), Item.CURRENT_USER);

                Response<Item> resp = api.submitItem(part, placeBody, commentBody, typeBody, catBody, authorBody).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    cb.onResult(resp.body(), false);
                } else {
                    cb.onError(new IllegalStateException("HTTP " + resp.code()));
                }
            } catch (IOException e) {
                cb.onResult(null, true);
            } catch (Exception e) {
                cb.onError(e);
            }
        });
    }

    public void getItemMessages(int itemId, Callback<List<com.example.loss.data.model.ChatMessage>> cb) {
        io.execute(() -> {
            try {
                Response<List<com.example.loss.data.model.ChatMessage>> resp = api.getItemMessages(itemId).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    cb.onResult(resp.body(), false);
                    return;
                }
            } catch (IOException e) {
                Log.w(TAG, "getItemMessages network error, fallback to offline demo messages: " + e.getMessage());
            } catch (Exception e) {
                cb.onError(e);
                return;
            }
            // Offline demo messages
            List<com.example.loss.data.model.ChatMessage> demo = new java.util.ArrayList<>();
            demo.add(new com.example.loss.data.model.ChatMessage(1, itemId, "Дежурный", "Здравствуйте! Вещь находится в учительской / каб. 204.", "10:15"));
            demo.add(new com.example.loss.data.model.ChatMessage(2, itemId, "Владелец", "Здравствуйте! Это точно моя вещь, смогу подойти после 4 урока.", "10:18"));
            cb.onResult(demo, true);
        });
    }

    public void postItemMessage(int itemId, String senderName, String text, Callback<com.example.loss.data.model.ChatMessage> cb) {
        io.execute(() -> {
            try {
                com.example.loss.data.model.ChatMessageRequest req = new com.example.loss.data.model.ChatMessageRequest(senderName, text);
                Response<com.example.loss.data.model.ChatMessage> resp = api.postItemMessage(itemId, req).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    cb.onResult(resp.body(), false);
                    return;
                }
            } catch (IOException e) {
                Log.w(TAG, "postItemMessage network error, offline fallback");
            } catch (Exception e) {
                cb.onError(e);
                return;
            }
            // Offline fallback
            com.example.loss.data.model.ChatMessage localMsg = new com.example.loss.data.model.ChatMessage(
                    (int) (System.currentTimeMillis() % 10000), itemId, senderName, text, "Только что");
            cb.onResult(localMsg, true);
        });
    }

    public void verifyReturnCode(int itemId, String code, Callback<com.example.loss.data.model.VerifyCodeResponse> cb) {
        io.execute(() -> {
            try {
                com.example.loss.data.model.VerifyCodeRequest req = new com.example.loss.data.model.VerifyCodeRequest(code);
                Response<com.example.loss.data.model.VerifyCodeResponse> resp = api.verifyReturnCode(itemId, req).execute();
                if (resp.isSuccessful() && resp.body() != null) {
                    cb.onResult(resp.body(), false);
                    return;
                }
            } catch (IOException e) {
                Log.w(TAG, "verifyReturnCode network error, fallback to offline check");
            } catch (Exception e) {
                cb.onError(e);
                return;
            }
            // Offline check
            for (Item it : loadLocal()) {
                if (it.id == itemId) {
                    if (it.returnCode != null && it.returnCode.trim().equals(code.trim())) {
                        cb.onResult(new com.example.loss.data.model.VerifyCodeResponse(true, "Код подтверждён (демо)! Статус вещи изменён на 'Возвращено'.", "returned"), true);
                    } else {
                        cb.onResult(new com.example.loss.data.model.VerifyCodeResponse(false, "Неверный код (демо). Попробуйте код из карточки.", it.status), true);
                    }
                    return;
                }
            }
            cb.onResult(new com.example.loss.data.model.VerifyCodeResponse(true, "Код подтверждён (демо)!", "returned"), true);
        });
    }

    public void createClaim(ClaimRequest req, Callback<Void> cb) {
        io.execute(() -> {
            try {
                Response<Void> resp = api.createClaim(req).execute();
                if (resp.isSuccessful()) {
                    cb.onResult(null, false);
                } else {
                    cb.onError(new IllegalStateException("HTTP " + resp.code()));
                }
            } catch (IOException e) {
                cb.onResult(null, true);
            } catch (Exception e) {
                cb.onError(e);
            }
        });
    }

    /**
     * Декодирует фото из content URI с downsampling, ресайзит до maxSide по длинной стороне,
     * жмёт в JPEG. На входе может быть фото 10–15 МБ, на выходе — обычно меньше 500 КБ.
     */
    private byte[] compressImage(Uri uri, int maxSide, int quality) throws IOException {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        try (InputStream in = appContext.getContentResolver().openInputStream(uri)) {
            if (in == null) throw new IOException("Не удалось открыть фото");
            BitmapFactory.decodeStream(in, null, bounds);
        }
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
            throw new IOException("Не удалось прочитать размеры изображения");
        }

        int longestSide = Math.max(bounds.outWidth, bounds.outHeight);
        int sample = 1;
        while (longestSide / (sample * 2) >= maxSide) sample *= 2;

        BitmapFactory.Options opts = new BitmapFactory.Options();
        opts.inSampleSize = sample;
        Bitmap bitmap;
        try (InputStream in = appContext.getContentResolver().openInputStream(uri)) {
            if (in == null) throw new IOException("Не удалось открыть фото");
            bitmap = BitmapFactory.decodeStream(in, null, opts);
        }
        if (bitmap == null) throw new IOException("Не удалось декодировать изображение");

        int w = bitmap.getWidth(), h = bitmap.getHeight();
        int longest = Math.max(w, h);
        if (longest > maxSide) {
            float scale = (float) maxSide / longest;
            Bitmap scaled = Bitmap.createScaledBitmap(
                    bitmap, Math.round(w * scale), Math.round(h * scale), true);
            if (scaled != bitmap) bitmap.recycle();
            bitmap = scaled;
        }

        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, out);
        bitmap.recycle();
        return out.toByteArray();
    }

    /**
     * Возвращает локальные данные с приоритетом:
     *   1. Кэш (то, что мобилка скачала в прошлый раз и сохранила).
     *   2. Бандлd-snapshot из assets/seed_items.json (положен при сборке APK).
     */
    private List<Item> loadLocal() {
        List<Item> cached = readCache();
        if (cached != null && !cached.isEmpty()) return cached;
        return loadSeed();
    }

    private List<Item> readCache() {
        File file = new File(appContext.getFilesDir(), CACHE_FILE);
        if (!file.exists()) return null;
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                new java.io.FileInputStream(file), StandardCharsets.UTF_8))) {
            return parseItems(r);
        } catch (IOException e) {
            Log.w(TAG, "Failed to read cache: " + e.getMessage());
            return null;
        }
    }

    private void writeCache(List<Item> items) {
        File file = new File(appContext.getFilesDir(), CACHE_FILE);
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(gson.toJson(items).getBytes(StandardCharsets.UTF_8));
        } catch (IOException e) {
            Log.w(TAG, "Failed to write cache: " + e.getMessage());
        }
    }

    private List<Item> loadSeed() {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                appContext.getAssets().open(SEED_FILE), StandardCharsets.UTF_8))) {
            return parseItems(r);
        } catch (IOException e) {
            Log.e(TAG, "Failed to load seed: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    private List<Item> parseItems(BufferedReader r) throws IOException {
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = r.readLine()) != null) sb.append(line);
        Type t = new TypeToken<List<Item>>(){}.getType();
        List<Item> items = gson.fromJson(sb.toString(), t);
        return items != null ? items : Collections.emptyList();
    }
}
