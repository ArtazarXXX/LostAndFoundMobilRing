package com.example.loss.data.model;

import com.google.gson.annotations.SerializedName;

public class ClaimRequest {
    @SerializedName("item_id")
    public final int itemId;
    public final String fio;
    @SerializedName("group_name")
    public final String groupName;
    public final String teacher;

    public ClaimRequest(int itemId, String fio, String groupName, String teacher) {
        this.itemId = itemId;
        this.fio = fio;
        this.groupName = groupName;
        this.teacher = teacher;
    }
}
