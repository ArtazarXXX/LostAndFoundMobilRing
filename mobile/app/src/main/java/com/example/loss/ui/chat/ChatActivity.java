package com.example.loss.ui.chat;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.loss.R;
import com.example.loss.data.model.ChatMessage;
import com.example.loss.data.repository.ItemsRepository;
import com.google.android.material.button.MaterialButton;

import java.util.List;

public class ChatActivity extends AppCompatActivity {

    public static final String EXTRA_ITEM_ID = "itemId";
    public static final String EXTRA_ITEM_TITLE = "itemTitle";

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ItemsRepository repo;
    private int itemId;
    private String currentUserName = "Я (Владелец)";

    private RecyclerView rv;
    private ChatMessageAdapter adapter;
    private EditText etMessage;
    private MaterialButton btnSend;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_chat);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);
        itemId = getIntent().getIntExtra(EXTRA_ITEM_ID, -1);
        String title = getIntent().getStringExtra(EXTRA_ITEM_TITLE);

        TextView txtTitle = findViewById(R.id.txtChatTitle);
        if (title != null && !title.isEmpty()) {
            txtTitle.setText("Диалог: " + title);
        }

        ImageButton btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());

        rv = findViewById(R.id.recyclerMessages);
        LinearLayoutManager lm = new LinearLayoutManager(this);
        lm.setStackFromEnd(true);
        rv.setLayoutManager(lm);

        adapter = new ChatMessageAdapter(currentUserName);
        rv.setAdapter(adapter);

        etMessage = findViewById(R.id.etMessage);
        btnSend = findViewById(R.id.btnSend);

        btnSend.setOnClickListener(v -> sendMessage());

        loadMessages();
    }

    private void loadMessages() {
        if (itemId <= 0) return;
        repo.getItemMessages(itemId, new ItemsRepository.Callback<List<ChatMessage>>() {
            @Override
            public void onResult(List<ChatMessage> value, boolean offline) {
                ui.post(() -> {
                    adapter.submit(value);
                    if (adapter.getItemCount() > 0) {
                        rv.scrollToPosition(adapter.getItemCount() - 1);
                    }
                });
            }

            @Override
            public void onError(Throwable error) {
                ui.post(() -> Toast.makeText(ChatActivity.this, "Ошибка загрузки: " + error.getMessage(), Toast.LENGTH_SHORT).show());
            }
        });
    }

    private void sendMessage() {
        String text = etMessage.getText().toString().trim();
        if (text.isEmpty() || itemId <= 0) return;

        etMessage.setText("");
        repo.postItemMessage(itemId, currentUserName, text, new ItemsRepository.Callback<ChatMessage>() {
            @Override
            public void onResult(ChatMessage value, boolean offline) {
                ui.post(() -> {
                    adapter.addMessage(value);
                    rv.smoothScrollToPosition(adapter.getItemCount() - 1);
                });
            }

            @Override
            public void onError(Throwable error) {
                ui.post(() -> Toast.makeText(ChatActivity.this, "Не удалось отправить: " + error.getMessage(), Toast.LENGTH_SHORT).show());
            }
        });
    }
}
