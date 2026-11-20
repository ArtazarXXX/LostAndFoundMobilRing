package com.example.loss.ui.claim;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.example.loss.R;
import com.example.loss.data.model.ClaimRequest;
import com.example.loss.data.repository.ItemsRepository;
import com.google.android.material.button.MaterialButton;

public class ClaimFormActivity extends AppCompatActivity {

    public static final String EXTRA_ITEM_ID = "itemId";

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ItemsRepository repo;
    private int itemId;
    private MaterialButton btnSend;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_form);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);
        itemId = getIntent().getIntExtra(EXTRA_ITEM_ID, -1);

        EditText etFio = findViewById(R.id.etFio);
        EditText etGroup = findViewById(R.id.etGroup);
        EditText etTeacher = findViewById(R.id.etTeacher);
        ImageButton btnBack = findViewById(R.id.btnBack);
        btnSend = findViewById(R.id.btnSend);

        btnBack.setOnClickListener(v -> finish());
        btnSend.setOnClickListener(v -> {
            String fio = etFio.getText().toString().trim();
            String group = etGroup.getText().toString().trim();
            String teacher = etTeacher.getText().toString().trim();
            if (fio.isEmpty() || group.isEmpty() || teacher.isEmpty()) {
                Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show();
                return;
            }
            if (itemId <= 0) {
                Toast.makeText(this, "Не выбран предмет", Toast.LENGTH_SHORT).show();
                return;
            }
            submit(new ClaimRequest(itemId, fio, group, teacher));
        });
    }

    private void submit(ClaimRequest req) {
        btnSend.setEnabled(false);
        repo.createClaim(req, new ItemsRepository.Callback<Void>() {
            @Override public void onResult(Void value, boolean offline) {
                ui.post(() -> {
                    String msg = offline
                            ? "Демо-режим: заявка не отправлена"
                            : "Заявка отправлена, ждите ответа админа";
                    Toast.makeText(ClaimFormActivity.this, msg, Toast.LENGTH_LONG).show();
                    finish();
                });
            }
            @Override public void onError(Throwable error) {
                ui.post(() -> {
                    btnSend.setEnabled(true);
                    Toast.makeText(ClaimFormActivity.this,
                            "Ошибка: " + error.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        });
    }
}
