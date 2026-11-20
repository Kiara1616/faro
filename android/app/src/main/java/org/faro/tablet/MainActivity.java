package org.faro.tablet;

import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;

import com.chaquo.python.Python;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String TAG = "FaroTablet";
    private final ExecutorService bootExecutor = Executors.newSingleThreadExecutor();
    private WebView webView;
    private TextView statusView;
    private int localPort = -1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(247, 248, 252));
        webView = new WebView(this);
        webView.setVisibility(View.GONE);
        root.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        statusView = new TextView(this);
        statusView.setText("Iniciando Faro…");
        statusView.setTextColor(Color.rgb(15, 23, 42));
        statusView.setTextSize(18);
        statusView.setGravity(Gravity.CENTER);
        root.addView(statusView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isLocal(request.getUrl());
            }
        });

        bootExecutor.execute(() -> {
            try {
                String url = Python.getInstance().getModule("faro_android")
                        .callAttr("start").toString();
                int port = Uri.parse(url).getPort();
                runOnUiThread(() -> {
                    if (isDestroyed()) return;
                    localPort = port;
                    webView.setVisibility(View.VISIBLE);
                    statusView.setVisibility(View.GONE);
                    webView.loadUrl(url);
                });
            } catch (Exception error) {
                Log.e(TAG, "No se pudo iniciar Faro", error);
                runOnUiThread(() -> {
                    if (!isDestroyed()) {
                        statusView.setText("No se pudo iniciar Faro. Revisa el registro de la aplicación.");
                    }
                });
            }
        });
    }

    private boolean isLocal(Uri uri) {
        return "http".equals(uri.getScheme())
                && "127.0.0.1".equals(uri.getHost())
                && uri.getPort() == localPort;
    }

    @Override
    protected void onDestroy() {
        bootExecutor.shutdownNow();
        webView.destroy();
        super.onDestroy();
    }
}
