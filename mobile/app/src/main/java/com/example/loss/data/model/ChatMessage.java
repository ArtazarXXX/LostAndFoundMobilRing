package com.example.loss.data.model;

import com.google.gson.annotations.SerializedName;

public class ChatMessage {
    public final int id;
    
    @SerializedName("item_id")
    public final int itemId;
    
    @SerializedName("sender_name")
    public final String senderName;
    
    public final String text;
    
    @SerializedName("created_at")
    public final String createdAt;

    public ChatMessage(int id, int itemId, String senderName, String text, String createdAt) {
        this.id = id;
        this.itemId = itemId;
        this.senderName = senderName;
        this.text = text;
        this.createdAt = createdAt != null ? createdAt : "";
    }
}
