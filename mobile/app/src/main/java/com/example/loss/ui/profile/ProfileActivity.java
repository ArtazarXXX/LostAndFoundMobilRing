package com.example.loss.ui.profile;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.loss.R;
import com.example.loss.data.model.Item;
import com.example.loss.data.repository.ItemsRepository;
import com.example.loss.ui.item.ItemActivity;
import com.example.loss.ui.main.ItemAdapter;

import java.util.ArrayList;
import java.util.List;

public class ProfileActivity extends AppCompatActivity {

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ItemsRepository repo;
    private ItemAdapter adapter;
    private TextView txtCountActive;
    private TextView txtCountReturned;
    private TextView txtEmpty;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_profile);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);

        ImageButton btnBack = findViewById(R.id.btnBack);
        btnBack.setOnClickListener(v -> finish());

        txtCountActive = findViewById(R.id.txtCountActive);
        txtCountReturned = findViewById(R.id.txtCountReturned);
        txtEmpty = findViewById(R.id.txtEmptyUserItems);

        RecyclerView rv = findViewById(R.id.recyclerUserItems);
        rv.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ItemAdapter(this::openItem);
        rv.setAdapter(adapter);

        loadProfileItems();
    }

    private void loadProfileItems() {
        repo.listAccepted(new ItemsRepository.Callback<List<Item>>() {
            @Override
            public void onResult(List<Item> value, boolean offline) {
                ui.post(() -> {
                    List<Item> userItems = new ArrayList<>();
                    int activeCount = 0;
                    int returnedCount = 0;

                    for (Item it : value) {
                        if (it.isOwnedByCurrentUser()) {
                            userItems.add(it);
                            if (it.isReturned()) {
                                returnedCount++;
                            } else {
                                activeCount++;
                            }
                        }
                    }

                    txtCountActive.setText(activeCount + " вещ.");
                    txtCountReturned.setText(returnedCount + " вещ.");

                    adapter.submit(userItems);
                    txtEmpty.setVisibility(userItems.isEmpty() ? View.VISIBLE : View.GONE);
                });
            }

            @Override
            public void onError(Throwable error) {
                ui.post(() -> txtEmpty.setVisibility(View.VISIBLE));
            }
        });
    }

    private void openItem(Item item) {
        Intent i = new Intent(this, ItemActivity.class);
        i.putExtra(ItemActivity.EXTRA_ITEM_ID, item.id);
        i.putExtra(ItemActivity.EXTRA_URL, item.url);
        i.putExtra(ItemActivity.EXTRA_PLACE, item.place);
        i.putExtra(ItemActivity.EXTRA_COMMENT, item.comment);
        i.putExtra(ItemActivity.EXTRA_TYPE, item.type);
        i.putExtra(ItemActivity.EXTRA_CATEGORY, item.category);
        i.putExtra(ItemActivity.EXTRA_STATUS, item.status);
        i.putExtra(ItemActivity.EXTRA_RETURN_CODE, item.returnCode);
        i.putExtra(ItemActivity.EXTRA_AUTHOR, item.author);
        startActivity(i);
    }
}
