package com.example.loss.data.api;

import com.example.loss.data.model.ChatMessage;
import com.example.loss.data.model.ChatMessageRequest;
import com.example.loss.data.model.ClaimRequest;
import com.example.loss.data.model.Item;
import com.example.loss.data.model.VerifyCodeRequest;
import com.example.loss.data.model.VerifyCodeResponse;

import java.util.List;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.Part;
import retrofit2.http.Path;
import retrofit2.http.Query;

public interface ApiService {

    @GET("users/items/getaccept")
    Call<List<Item>> listAccepted(
            @Query("type") String type,
            @Query("category") String category
    );

    @GET("users/items/getitem/{id}")
    Call<Item> getItem(@Path("id") int id);

    @POST("users/claims")
    Call<Void> createClaim(@Body ClaimRequest request);

    @Multipart
    @POST("users/items")
    Call<Item> submitItem(
            @Part MultipartBody.Part photo,
            @Part("place") RequestBody place,
            @Part("comment") RequestBody comment,
            @Part("type") RequestBody type,
            @Part("category") RequestBody category,
            @Part("author") RequestBody author
    );

    @GET("users/items/{id}/messages")
    Call<List<ChatMessage>> getItemMessages(@Path("id") int id);

    @POST("users/items/{id}/messages")
    Call<ChatMessage> postItemMessage(@Path("id") int id, @Body ChatMessageRequest request);

    @POST("users/items/{id}/verify_code")
    Call<VerifyCodeResponse> verifyReturnCode(@Path("id") int id, @Body VerifyCodeRequest request);
}

