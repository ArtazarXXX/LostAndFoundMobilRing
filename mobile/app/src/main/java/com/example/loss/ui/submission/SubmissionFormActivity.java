package com.example.loss.ui.submission;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.PickVisualMediaRequest;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.bumptech.glide.Glide;
import com.example.loss.R;
import com.example.loss.data.model.Item;
import com.example.loss.data.repository.ItemsRepository;
import com.google.android.material.button.MaterialButton;

public class SubmissionFormActivity extends AppCompatActivity {

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ItemsRepository repo;
    private Uri photoUri;

    private ImageView imgPreview;
    private TextView txtPickLabel;
    private MaterialButton btnSend;
    private RadioGroup rgType;
    private RadioButton rbLost;
    private Spinner spinnerCategory;

    private static final String[] CATEGORY_KEYS = {"clothes", "keys", "cards", "tech", "other"};
    private static final String[] CATEGORY_LABELS = {
            "👟 Сменка и одежда",
            "🔑 Ключи",
            "💳 Карты и пропуска",
            "📱 Электроника",
            "📦 Другое"
    };

    private final ActivityResultLauncher<PickVisualMediaRequest> picker =
            registerForActivityResult(new ActivityResultContracts.PickVisualMedia(), uri -> {
                if (uri != null) {
                    photoUri = uri;
                    imgPreview.setVisibility(View.VISIBLE);
                    Glide.with(this).load(uri).centerCrop().into(imgPreview);
                    txtPickLabel.setText("заменить фото");
                }
            });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_submission);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);

        ImageButton btnBack = findViewById(R.id.btnBack);
        LinearLayout btnPick = findViewById(R.id.btnPickPhoto);
        imgPreview = findViewById(R.id.imgPhotoPreview);
        txtPickLabel = findViewById(R.id.txtPickPhoto);
        btnSend = findViewById(R.id.btnSend);
        EditText etComment = findViewById(R.id.etComment);
        EditText etPlace = findViewById(R.id.etPlace);
        rgType = findViewById(R.id.rgType);
        rbLost = findViewById(R.id.rbLost);
        spinnerCategory = findViewById(R.id.spinnerCategory);

        ArrayAdapter<String> catAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_dropdown_item, CATEGORY_LABELS);
        spinnerCategory.setAdapter(catAdapter);

        btnBack.setOnClickListener(v -> finish());
        btnPick.setOnClickListener(v -> picker.launch(new PickVisualMediaRequest.Builder()
                .setMediaType(ActivityResultContracts.PickVisualMedia.ImageOnly.INSTANCE)
                .build()));

        btnSend.setOnClickListener(v -> {
            String comment = etComment.getText().toString().trim();
            String place = etPlace.getText().toString().trim();
            if (photoUri == null) {
                Toast.makeText(this, "Добавьте фото", Toast.LENGTH_SHORT).show();
                return;
            }
            if (comment.isEmpty() || place.isEmpty()) {
                Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show();
                return;
            }
            String type = rbLost.isChecked() ? "lost" : "found";
            int selectedCatPos = spinnerCategory.getSelectedItemPosition();
            String category = (selectedCatPos >= 0 && selectedCatPos < CATEGORY_KEYS.length)
                    ? CATEGORY_KEYS[selectedCatPos] : "other";

            submit(photoUri, place, comment, type, category);
        });
    }

    private void submit(Uri uri, String place, String comment, String type, String category) {
        btnSend.setEnabled(false);
        repo.submitItem(uri, place, comment, type, category, new ItemsRepository.Callback<Item>() {
            @Override public void onResult(Item value, boolean offline) {
                ui.post(() -> {
                    String msg = offline
                            ? "Демо-режим: объявление добавлено в локальный список"
                            : "Объявление успешно опубликовано!";
                    Toast.makeText(SubmissionFormActivity.this, msg, Toast.LENGTH_LONG).show();
                    finish();
                });
            }
            @Override public void onError(Throwable error) {
                ui.post(() -> {
                    btnSend.setEnabled(true);
                    Toast.makeText(SubmissionFormActivity.this,
                            "Ошибка: " + error.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        });
    }
}

