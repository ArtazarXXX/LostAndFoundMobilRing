package com.example.loss.ui.main;

import android.content.Context;
import android.content.res.ColorStateList;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.bumptech.glide.Glide;
import com.example.loss.R;
import com.example.loss.data.ImageUrls;
import com.example.loss.data.model.Item;

import java.util.ArrayList;
import java.util.List;

public class ItemAdapter extends RecyclerView.Adapter<ItemAdapter.VH> {

    public interface OnItemClick {
        void onClick(Item item);
    }

    private final List<Item> data = new ArrayList<>();
    private final OnItemClick clickHandler;

    public ItemAdapter(OnItemClick clickHandler) {
        this.clickHandler = clickHandler;
    }

    public void submit(List<Item> items) {
        data.clear();
        if (items != null) data.addAll(items);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_card, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int pos) {
        Item it = data.get(pos);
        Context ctx = h.itemView.getContext();

        h.txtPlace.setText(it.place);
        h.txtComment.setText(it.comment);

        // Bind type badge
        if (it.isLost()) {
            h.badgeType.setText("ПРОПАЖА");
            h.badgeType.setTextColor(ContextCompat.getColor(ctx, R.color.badge_lost));
            h.badgeType.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(ctx, R.color.badge_lost_bg)));
        } else {
            h.badgeType.setText("НАХОДКА");
            h.badgeType.setTextColor(ContextCompat.getColor(ctx, R.color.badge_found));
            h.badgeType.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(ctx, R.color.badge_found_bg)));
        }

        // Bind status badge
        if (it.isReturned()) {
            h.badgeStatus.setText("ВОЗВРАЩЕНО");
            h.badgeStatus.setTextColor(ContextCompat.getColor(ctx, R.color.status_returned));
            h.badgeStatus.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(ctx, R.color.status_returned_bg)));
        } else {
            h.badgeStatus.setText("ИЩЕТ ВЛАДЕЛЬЦА");
            h.badgeStatus.setTextColor(ContextCompat.getColor(ctx, R.color.status_active));
            h.badgeStatus.setBackgroundTintList(ColorStateList.valueOf(ContextCompat.getColor(ctx, R.color.status_active_bg)));
        }

        // Bind category
        h.txtCategory.setText(getCategoryLabel(it.category));

        // Bind date
        h.txtDate.setText(it.createdAt != null && !it.createdAt.isEmpty() ? it.createdAt : "Недавно");

        Glide.with(ctx)
                .load(ImageUrls.resolve(it.url))
                .placeholder(R.drawable.bg_image_placeholder)
                .error(R.drawable.bg_image_placeholder)
                .centerCrop()
                .into(h.imgItem);

        h.itemView.setOnClickListener(v -> clickHandler.onClick(it));
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

    @Override
    public int getItemCount() {
        return data.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        final ImageView imgItem;
        final TextView badgeType;
        final TextView badgeStatus;
        final TextView txtCategory;
        final TextView txtDate;
        final TextView txtPlace;
        final TextView txtComment;

        VH(View v) {
            super(v);
            imgItem = v.findViewById(R.id.imgItem);
            badgeType = v.findViewById(R.id.badgeType);
            badgeStatus = v.findViewById(R.id.badgeStatus);
            txtCategory = v.findViewById(R.id.txtCategory);
            txtDate = v.findViewById(R.id.txtDate);
            txtPlace = v.findViewById(R.id.txtPlace);
            txtComment = v.findViewById(R.id.txtComment);
        }
    }
}

