package com.example.loss.data.model;

import com.google.gson.annotations.SerializedName;

public class ChatMessageRequest {
    @SerializedName("sender_name")
    public final String senderName;
    public final String text;

    public ChatMessageRequest(String senderName, String text) {
        this.senderName = senderName;
        this.text = text;
    }
}
