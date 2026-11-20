package com.example.loss.ui.chat;

import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.example.loss.R;
import com.example.loss.data.model.ChatMessage;

import java.util.ArrayList;
import java.util.List;

public class ChatMessageAdapter extends RecyclerView.Adapter<ChatMessageAdapter.VH> {

    private final List<ChatMessage> list = new ArrayList<>();
    private final String currentUserName;

    public ChatMessageAdapter(String currentUserName) {
        this.currentUserName = currentUserName;
    }

    public void submit(List<ChatMessage> messages) {
        list.clear();
        if (messages != null) list.addAll(messages);
        notifyDataSetChanged();
    }

    public void addMessage(ChatMessage msg) {
        list.add(msg);
        notifyItemInserted(list.size() - 1);
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_chat_message, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int pos) {
        ChatMessage m = list.get(pos);
        h.txtSender.setText(m.senderName);
        h.txtMessage.setText(m.text);
        h.txtTime.setText(m.createdAt != null && !m.createdAt.isEmpty() ? m.createdAt : "Сейчас");

        boolean isMe = currentUserName != null && currentUserName.equalsIgnoreCase(m.senderName);
        LinearLayout.LayoutParams params = (LinearLayout.LayoutParams) h.layoutBubble.getLayoutParams();

        if (isMe) {
            params.gravity = Gravity.END;
            h.layoutBubble.setBackground(ContextCompat.getDrawable(h.itemView.getContext(), R.drawable.bg_chat_me));
        } else {
            params.gravity = Gravity.START;
            h.layoutBubble.setBackground(ContextCompat.getDrawable(h.itemView.getContext(), R.drawable.bg_chat_other));
        }
        h.layoutBubble.setLayoutParams(params);
    }

    @Override
    public int getItemCount() {
        return list.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        final LinearLayout layoutBubble;
        final TextView txtSender;
        final TextView txtMessage;
        final TextView txtTime;

        VH(View v) {
            super(v);
            layoutBubble = v.findViewById(R.id.layoutBubble);
            txtSender = v.findViewById(R.id.txtSender);
            txtMessage = v.findViewById(R.id.txtMessage);
            txtTime = v.findViewById(R.id.txtTime);
        }
    }
}
