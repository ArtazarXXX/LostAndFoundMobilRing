package com.example.loss.ui.item;

import android.content.Context;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.bumptech.glide.Glide;
import com.example.loss.R;
import com.example.loss.data.ImageUrls;
import com.example.loss.data.model.Item;
import com.example.loss.data.model.VerifyCodeResponse;
import com.example.loss.data.repository.ItemsRepository;
import com.example.loss.ui.chat.ChatActivity;
import com.example.loss.ui.claim.ClaimFormActivity;
import com.google.android.material.button.MaterialButton;

public class ItemActivity extends AppCompatActivity {

    public static final String EXTRA_ITEM_ID = "itemId";
    public static final String EXTRA_URL = "url";
    public static final String EXTRA_PLACE = "place";
    public static final String EXTRA_COMMENT = "comment";
    public static final String EXTRA_TYPE = "type";
    public static final String EXTRA_CATEGORY = "category";
    public static final String EXTRA_STATUS = "status";
    public static final String EXTRA_RETURN_CODE = "returnCode";
    public static final String EXTRA_AUTHOR = "author";

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ItemsRepository repo;
    private int itemId;
    private String currentStatus;
    private String author;
    private String returnCode;

    private TextView badgeStatus;
    private TextView txtHandoverTitle;
    private TextView txtAuthorLabel;
    private TextView txtCodePrompt;
    private TextView txtReturnCode;
    private TextView txtAuthorNotice;
    private MaterialButton btnVerifyCode;
    private MaterialButton btnChat;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_item);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);

        Intent intent = getIntent();
        itemId = intent.getIntExtra(EXTRA_ITEM_ID, -1);
        String url = intent.getStringExtra(EXTRA_URL);
        String place = intent.getStringExtra(EXTRA_PLACE);
        String comment = intent.getStringExtra(EXTRA_COMMENT);
        String type = intent.getStringExtra(EXTRA_TYPE);
        String category = intent.getStringExtra(EXTRA_CATEGORY);
        currentStatus = intent.getStringExtra(EXTRA_STATUS);
        returnCode = intent.getStringExtra(EXTRA_RETURN_CODE);
        author = intent.getStringExtra(EXTRA_AUTHOR);
        if (author == null || author.isEmpty()) {
            author = "Дежурный";
        }

        ImageView img = findViewById(R.id.imgLostThing);
        TextView txtOpisanie = findViewById(R.id.txtOpisanie);
        TextView txtPlace = findViewById(R.id.txtPlace);
        TextView badgeType = findViewById(R.id.badgeType);
        badgeStatus = findViewById(R.id.badgeStatus);
        TextView badgeCategory = findViewById(R.id.badgeCategory);
        txtHandoverTitle = findViewById(R.id.txtHandoverTitle);
        txtAuthorLabel = findViewById(R.id.txtAuthorLabel);
        txtCodePrompt = findViewById(R.id.txtCodePrompt);
        txtReturnCode = findViewById(R.id.txtReturnCode);
        txtAuthorNotice = findViewById(R.id.txtAuthorNotice);
        btnVerifyCode = findViewById(R.id.btnVerifyCode);
        ImageButton btnBack = findViewById(R.id.btnBack);
        btnChat = findViewById(R.id.btnChat);
        MaterialButton btnMy = findViewById(R.id.btnMy);

        Glide.with(this)
                .load(ImageUrls.resolve(url))
                .placeholder(R.drawable.bg_image_placeholder)
                .error(R.drawable.bg_image_placeholder)
                .centerCrop()
                .into(img);
        txtOpisanie.setText(comment);
        txtPlace.setText(place);

        // Type badge
        boolean isLost = "lost".equalsIgnoreCase(type);
        if (isLost) {
            badgeType.setText("ПРОПАЖА");
            badgeType.setTextColor(ContextCompat.getColor(this, R.color.badge_lost));
            badgeType.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(this, R.color.badge_lost_bg)));
        } else {
            badgeType.setText("НАХОДКА");
            badgeType.setTextColor(ContextCompat.getColor(this, R.color.badge_found));
            badgeType.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(this, R.color.badge_found_bg)));
        }

        // Category badge
        badgeCategory.setText(getCategoryLabel(category));

        // Update Handover and Status view
        updateHandoverUI();

        btnBack.setOnClickListener(v -> finish());

        boolean isOwner = isCurrentUserAuthor();
        btnChat.setText(isOwner ? "💬 Сообщения по объявлению" : "💬 Написать автору (" + author + ")");
        btnChat.setOnClickListener(v -> {
            Intent i = new Intent(this, ChatActivity.class);
            i.putExtra(ChatActivity.EXTRA_ITEM_ID, itemId);
            i.putExtra(ChatActivity.EXTRA_ITEM_TITLE, comment);
            startActivity(i);
        });

        btnVerifyCode.setOnClickListener(v -> showVerifyCodeDialog());

        btnMy.setOnClickListener(v -> {
            Intent i = new Intent(this, ClaimFormActivity.class);
            i.putExtra(ClaimFormActivity.EXTRA_ITEM_ID, itemId);
            startActivity(i);
        });
    }

    private boolean isCurrentUserAuthor() {
        if (author == null) return false;
        return Item.CURRENT_USER.equalsIgnoreCase(author.trim())
                || author.toLowerCase().contains("кабанов");
    }

    private void updateHandoverUI() {
        boolean isReturned = "returned".equalsIgnoreCase(currentStatus);
        boolean isOwner = isCurrentUserAuthor();

        if (isReturned) {
            badgeStatus.setText("ВОЗВРАЩЕНО");
            badgeStatus.setTextColor(ContextCompat.getColor(this, R.color.status_returned));
            badgeStatus.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(this, R.color.status_returned_bg)));

            txtHandoverTitle.setText("✅ Вещь успешно возвращена");
            txtAuthorLabel.setText(isOwner ? "👤 Ваше объявление" : "👤 Автор: " + author);
            txtCodePrompt.setText("Сделка закрыта через безопасную передачу.");
            txtReturnCode.setVisibility(View.GONE);
            txtAuthorNotice.setVisibility(View.GONE);
            btnVerifyCode.setVisibility(View.VISIBLE);
            btnVerifyCode.setEnabled(false);
            btnVerifyCode.setText("Вещь передана владельцу");
        } else if (isOwner) {
            badgeStatus.setText("ИЩЕТ ВЛАДЕЛЬЦА");
            badgeStatus.setTextColor(ContextCompat.getColor(this, R.color.status_active));
            badgeStatus.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(this, R.color.status_active_bg)));

            txtHandoverTitle.setText("🔒 Ваш секретный проверочный код");
            txtAuthorLabel.setText("👤 Вы разместили это объявление");
            txtCodePrompt.setText("Назовите этот проверочный код получателю при встрече:");
            txtReturnCode.setVisibility(View.VISIBLE);
            String displayCode = returnCode != null && !returnCode.isEmpty() ? returnCode : "4821";
            txtReturnCode.setText(displayCode);

            txtAuthorNotice.setVisibility(View.VISIBLE);
            txtAuthorNotice.setText("ℹ️ Вы автор объявления. Назовите этот код получателю при передаче вещи. Получатель введёт его в своём приложении, и статус вещи автоматически станет «Возвращено».");

            // Author cannot return the item to himself!
            btnVerifyCode.setVisibility(View.GONE);
        } else {
            badgeStatus.setText("ИЩЕТ ВЛАДЕЛЬЦА");
            badgeStatus.setTextColor(ContextCompat.getColor(this, R.color.status_active));
            badgeStatus.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(this, R.color.status_active_bg)));

            txtHandoverTitle.setText("🔒 Безопасная передача вещи");
            txtAuthorLabel.setText("👤 Автор объявления: " + author);
            txtCodePrompt.setText("Получаете вещь у автора? Попросите его назвать проверочный код:");
            txtReturnCode.setVisibility(View.GONE);
            txtAuthorNotice.setVisibility(View.GONE);

            btnVerifyCode.setVisibility(View.VISIBLE);
            btnVerifyCode.setEnabled(true);
            btnVerifyCode.setText("Ввести проверочный код от автора");
        }
    }

    private void showVerifyCodeDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Подтверждение возврата");
        builder.setMessage("Введите 4-значный проверочный код, полученный от автора объявления (" + author + "):");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER);
        input.setHint("Например: 7392");
        builder.setView(input);

        builder.setPositiveButton("Подтвердить", (dialog, which) -> {
            String entered = input.getText().toString().trim();
            if (entered.isEmpty()) return;
            verifyCode(entered);
        });
        builder.setNegativeButton("Отмена", (dialog, which) -> dialog.cancel());
        builder.show();
    }

    private void verifyCode(String code) {
        repo.verifyReturnCode(itemId, code, new ItemsRepository.Callback<VerifyCodeResponse>() {
            @Override
            public void onResult(VerifyCodeResponse value, boolean offline) {
                ui.post(() -> {
                    if (value.success) {
                        currentStatus = "returned";
                        updateHandoverUI();
                        new AlertDialog.Builder(ItemActivity.this)
                                .setTitle("Успешный возврат!")
                                .setMessage(value.message)
                                .setPositiveButton("Отлично", null)
                                .show();
                    } else {
                        Toast.makeText(ItemActivity.this, value.message, Toast.LENGTH_LONG).show();
                    }
                });
            }

            @Override
            public void onError(Throwable error) {
                ui.post(() -> Toast.makeText(ItemActivity.this, "Ошибка проверки: " + error.getMessage(), Toast.LENGTH_SHORT).show());
            }
        });
    }

    private String getCategoryLabel(String cat) {
        if (cat == null) return "📦 Другое";
        switch (cat.toLowerCase()) {
            case "clothes": return "👟 Сменка и одежда";
            case "keys": return "🔑 Ключи";
            case "cards": return "💳 Карты и пропуска";
            case "tech": return "📱 Электроника";
            default: return "📦 Разное";
        }
    }
}
