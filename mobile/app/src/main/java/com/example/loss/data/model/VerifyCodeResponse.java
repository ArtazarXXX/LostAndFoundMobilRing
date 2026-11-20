package com.example.loss.data.model;

public class VerifyCodeResponse {
    public final boolean success;
    public final String message;
    public final String status;

    public VerifyCodeResponse(boolean success, String message, String status) {
        this.success = success;
        this.message = message;
        this.status = status;
    }
}
