package com.example.loss.data.model;

import com.google.gson.annotations.SerializedName;

public class Item {
    public static final String CURRENT_USER = "Максим Кабанов";

    public final int id;
    public final String url;
    public final String place;
    public final String comment;
    public final String status;
    public final String type; // "found" or "lost"
    public final String category; // "clothes", "keys", "cards", "tech", "other"
    
    @SerializedName("return_code")
    public final String returnCode;
    
    @SerializedName("created_at")
    public final String createdAt;

    public final String author;

    public Item(int id, String url, String place, String comment, String status, String type, String category, String returnCode, String createdAt, String author) {
        this.id = id;
        this.url = url;
        this.place = place;
        this.comment = comment;
        this.status = status;
        this.type = type != null ? type : "found";
        this.category = category != null ? category : "other";
        this.returnCode = returnCode != null ? returnCode : "1234";
        this.createdAt = createdAt != null ? createdAt : "";
        this.author = author != null && !author.isEmpty() ? author : "Дежурный";
    }

    public Item(int id, String url, String place, String comment, String status, String type, String category, String returnCode, String createdAt) {
        this(id, url, place, comment, status, type, category, returnCode, createdAt, "Дежурный");
    }

    public boolean isLost() {
        return "lost".equalsIgnoreCase(type);
    }

    public boolean isReturned() {
        return "returned".equalsIgnoreCase(status);
    }

    public boolean isOwnedByCurrentUser() {
        if (author == null) return false;
        return CURRENT_USER.equalsIgnoreCase(author.trim()) || author.toLowerCase().contains("кабанов");
    }
}
