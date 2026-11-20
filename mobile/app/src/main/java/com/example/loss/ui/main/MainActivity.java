package com.example.loss.ui.main;

import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import com.example.loss.R;
import com.example.loss.data.model.Item;
import com.example.loss.data.repository.ItemsRepository;
import com.example.loss.ui.item.ItemActivity;
import com.example.loss.ui.profile.ProfileActivity;
import com.example.loss.ui.submission.SubmissionFormActivity;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private ItemsRepository repo;
    private ItemAdapter adapter;
    private SwipeRefreshLayout swipe;
    private TextView bannerOffline;
    private TextView txtEmpty;
    private EditText etSearch;

    private TextView tabFound;
    private TextView tabLost;
    private String selectedType = "found"; // "found" or "lost"
    private String selectedCategory = "all"; // "all", "clothes", "keys", "cards", "tech", "other"

    private TextView[] categoryChips;
    private final String[] categoryKeys = {"all", "clothes", "keys", "cards", "tech", "other"};

    private final List<Item> all = new ArrayList<>();
    private final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets sb = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(sb.left, sb.top, sb.right, sb.bottom);
            return insets;
        });

        repo = new ItemsRepository(this);
        swipe = findViewById(R.id.swipe);
        bannerOffline = findViewById(R.id.bannerOffline);
        txtEmpty = findViewById(R.id.txtEmpty);
        etSearch = findViewById(R.id.etSearch);

        tabFound = findViewById(R.id.tabFound);
        tabLost = findViewById(R.id.tabLost);

        setupTabs();
        setupChips();

        findViewById(R.id.btnProfile).setOnClickListener(v ->
                startActivity(new Intent(this, ProfileActivity.class)));

        RecyclerView rv = findViewById(R.id.recyclerItems);
        rv.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ItemAdapter(this::openItem);
        rv.setAdapter(adapter);

        findViewById(R.id.addBanner).setOnClickListener(v ->
                startActivity(new Intent(this, SubmissionFormActivity.class)));

        swipe.setOnRefreshListener(this::load);

        etSearch.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable s) {
                applyFilter(s.toString());
            }
        });

        load();
    }

    @Override
    protected void onResume() {
        super.onResume();
        load();
    }

    private void setupTabs() {
        tabFound.setOnClickListener(v -> {
            selectedType = "found";
            updateTabStyles();
            applyFilter(etSearch.getText().toString());
        });

        tabLost.setOnClickListener(v -> {
            selectedType = "lost";
            updateTabStyles();
            applyFilter(etSearch.getText().toString());
        });
        updateTabStyles();
    }

    private void updateTabStyles() {
        boolean isFound = "found".equalsIgnoreCase(selectedType);
        if (isFound) {
            tabFound.setBackground(ContextCompat.getDrawable(this, R.drawable.bg_badge_rounded));
            tabFound.setBackgroundTintList(ColorStateList.valueOf(Color.WHITE));
            tabFound.setTextColor(Color.parseColor("#0F172A"));

            tabLost.setBackground(null);
            tabLost.setTextColor(Color.parseColor("#64748B"));
        } else {
            tabLost.setBackground(ContextCompat.getDrawable(this, R.drawable.bg_badge_rounded));
            tabLost.setBackgroundTintList(ColorStateList.valueOf(Color.WHITE));
            tabLost.setTextColor(Color.parseColor("#0F172A"));

            tabFound.setBackground(null);
            tabFound.setTextColor(Color.parseColor("#64748B"));
        }
    }

    private void setupChips() {
        categoryChips = new TextView[] {
                findViewById(R.id.chipAll),
                findViewById(R.id.chipClothes),
                findViewById(R.id.chipKeys),
                findViewById(R.id.chipCards),
                findViewById(R.id.chipTech),
                findViewById(R.id.chipOther)
        };

        for (int i = 0; i < categoryChips.length; i++) {
            final String catKey = categoryKeys[i];
            categoryChips[i].setOnClickListener(v -> {
                selectedCategory = catKey;
                updateChipsStyles();
                applyFilter(etSearch.getText().toString());
            });
        }
        updateChipsStyles();
    }

    private void updateChipsStyles() {
        int brandBlue = ContextCompat.getColor(this, R.color.brand_blue);
        for (int i = 0; i < categoryChips.length; i++) {
            boolean active = categoryKeys[i].equalsIgnoreCase(selectedCategory);
            if (active) {
                categoryChips[i].setBackgroundTintList(ColorStateList.valueOf(brandBlue));
                categoryChips[i].setTextColor(Color.BLACK);
            } else {
                categoryChips[i].setBackgroundTintList(ColorStateList.valueOf(Color.WHITE));
                categoryChips[i].setTextColor(Color.parseColor("#475569"));
            }
        }
    }

    private void load() {
        swipe.setRefreshing(true);
        repo.listAccepted(new ItemsRepository.Callback<List<Item>>() {
            @Override public void onResult(List<Item> value, boolean offline) {
                ui.post(() -> {
                    swipe.setRefreshing(false);
                    bannerOffline.setVisibility(offline ? View.VISIBLE : View.GONE);
                    all.clear();
                    all.addAll(value);
                    applyFilter(etSearch.getText().toString());
                });
            }
            @Override public void onError(Throwable error) {
                ui.post(() -> {
                    swipe.setRefreshing(false);
                    Toast.makeText(MainActivity.this,
                            "Не удалось загрузить: " + error.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        });
    }

    private void applyFilter(String query) {
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        List<Item> filtered = new ArrayList<>();

        for (Item it : all) {
            // Type filter
            boolean matchType = selectedType.equalsIgnoreCase(it.type);
            if (!matchType) continue;

            // Category filter
            boolean matchCategory = "all".equalsIgnoreCase(selectedCategory)
                    || selectedCategory.equalsIgnoreCase(it.category);
            if (!matchCategory) continue;

            // Search query filter
            boolean matchQuery = q.isEmpty()
                    || it.place.toLowerCase(Locale.ROOT).contains(q)
                    || it.comment.toLowerCase(Locale.ROOT).contains(q);

            if (matchQuery) {
                filtered.add(it);
            }
        }

        adapter.submit(filtered);
        txtEmpty.setVisibility(filtered.isEmpty() ? View.VISIBLE : View.GONE);
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

