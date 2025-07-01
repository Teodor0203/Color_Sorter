package com.example.testing;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

public class ConnectionManager implements DataCallback {

    //region TAG and UUID
    private final String TAG = "ConnectionManager";
    private final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    //endregion

    //region Handler and BluetoothAdapter
    private Handler handler = new Handler(Looper.getMainLooper());
    private BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();// UUID for SPP
    //endregion

    //region booleans
    private boolean isConnected = false;
    //endregion

    //region other
    private static ConnectionManager INSTANCE;
    private Context context;
    private BluetoothSocket bluetoothSocket;
    private InputStream inputStream;
    private OutputStream outpustStream;
    private ProgressBar progressBar;
    private TextView textView;
    private Button startButton;
    //endregion

    public ConnectionManager(Context context, ProgressBar progressBar, TextView textView, Button startButton) {
        this.context = context;
        this.progressBar = progressBar;
        this.textView = textView;
        this.startButton = startButton;
        checkIfBluetoothIsSupported();
    }

    public ConnectionManager() {
        checkIfBluetoothIsSupported();
    }

    public static ConnectionManager getInstance() {
        if (INSTANCE == null) {
            INSTANCE = new ConnectionManager();
        }

        return INSTANCE;
    }

    public static ConnectionManager getInstance(Context context, ProgressBar progressBar, TextView textView, Button startButton) {
        if (INSTANCE == null) {
            INSTANCE = new ConnectionManager(context, progressBar, textView, startButton);
        }

        return INSTANCE;
    }

    public void checkIfBluetoothIsSupported() {
        if (adapter == null) {
            Toast.makeText(context, "Bluetooth is not supported!!", Toast.LENGTH_LONG).show();
        }
    }

    @SuppressLint("MissingPermission")
    public void enableBluetooth(Activity activity) {
        if (!adapter.isEnabled()) {
            Log.d(TAG, "onEnable: Enabling bluetooth");
            Intent intent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE); //Request to enable Bluetooth
            activity.startActivityForResult(intent, 1);

            BroadcastReceiver receiver = new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    if (BluetoothAdapter.ACTION_STATE_CHANGED.equals(intent.getAction())) {
                        int state = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, BluetoothAdapter.ERROR);
                        if (state == BluetoothAdapter.STATE_ON) {  //Check if Bluetooth is now enabled
                            Log.d(TAG, "Bluetooth activated");
                            context.unregisterReceiver(this); //Unregister receiver to prevent memory leaks
                            ((Activity) context).runOnUiThread(() -> //Update UI
                                    Toast.makeText(context, "Looking for device!", Toast.LENGTH_LONG).show()
                            );
                            connectToPI();
                        }
                    }
                }
            };
            IntentFilter filter = new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED); //
            activity.registerReceiver(receiver, filter); //Register the receiver
        }
    }

    public void disconnect() {
        //Disconnect the Bluetooth socket
        try {
            if (bluetoothSocket != null) {
                bluetoothSocket.close();
                bluetoothSocket = null;
                isConnected = false;
                Log.d(TAG, "Disconnected");
            }
        } catch (IOException e) {
            Log.e(TAG, "Error closing connection: " + e.getMessage());
        }
    }

    @SuppressLint("MissingPermission")
    private BroadcastReceiver discoveryReceiver;
    private boolean receiverAlreadyUnregistered = false;

    @SuppressLint("MissingPermission")
    public void connectToPI() {
        final String targetMacAddress = "2C:CF:67:DB:D2:80"; // ← MAC-ul Pi-ului

        this.context = context;


        // UI update


        try {
            BluetoothDevice device = adapter.getRemoteDevice(targetMacAddress);
            connectToDevice(device); // ← Funcția ta deja existentă pentru conectare



            ((Activity) context).runOnUiThread(() ->
                    Toast.makeText(context, "Connected to " + device.getName(), Toast.LENGTH_SHORT).show()
            );
        } catch (IllegalArgumentException e) {


            Log.e(TAG, "Invalid MAC address", e);
        } catch (Exception e) {

            Log.e(TAG, "Connection failed", e);
        }
    }


    // Funcție utilitară ca să evităm excepțiile
    private void safeUnregisterReceiver(Context context) {
        if (!receiverAlreadyUnregistered && discoveryReceiver != null) {
            try {
                context.unregisterReceiver(discoveryReceiver);
            } catch (IllegalArgumentException e) {
                Log.w(TAG, "Receiver already unregistered.");
            }
            receiverAlreadyUnregistered = true;
        }
    }


    @SuppressLint("MissingPermission")
    private void connectToDevice(BluetoothDevice device) {
        if (bluetoothSocket != null && bluetoothSocket.isConnected()) {
            disconnect();
        }

        try {
            // Creează socket pe portul 2, fără SDP
            bluetoothSocket = (BluetoothSocket) device.getClass()
                    .getMethod("createRfcommSocket", new Class[]{int.class})
                    .invoke(device, 2);

            bluetoothSocket.connect();

            if (bluetoothSocket != null && bluetoothSocket.isConnected()) {
                inputStream = bluetoothSocket.getInputStream(); // Initializează InputStream
                outpustStream = bluetoothSocket.getOutputStream();
                isConnected = true;
                Log.d(TAG, "Conectat cu succes și inputStream inițializat.");

                if (textView != null) {
                    textView.setText("Connected ✔");
                }

                if (startButton != null) {
                    startButton.setVisibility(View.VISIBLE);
                }

            } else {
                Log.e(TAG, "Socket conectat eșuat.");
                if (textView != null) {
                    textView.setText("Connection failed\n:(");
                }
            }

        } catch (Exception e) {
            Log.e(TAG, "Eroare la conectare: " + e.getMessage());
            e.printStackTrace();

            if (progressBar != null) {
                progressBar.setVisibility(View.INVISIBLE);
            }

            if (textView != null) {
                textView.setText("Connection failed\n:(");
            }

            if (startButton != null) {
                startButton.setVisibility(View.INVISIBLE);
            }

            try {
                if (bluetoothSocket != null) {
                    bluetoothSocket.close();
                }
            } catch (IOException closeException) {
                Log.e(TAG, "Eroare la închiderea socket-ului: " + closeException.getMessage());
            }
        }
    }

    public void sendData(String data)
    {
        if(outpustStream != null && isConnected)
        {
            try
            {
                outpustStream.write(data.getBytes());
                outpustStream.flush();
            }
            catch (IOException e)
            {
                Log.e(TAG, "Error: " + e.getMessage());
            }
        }
        else {
            Log.e("FragmentConnection", "OutputStream not initialized!");
        }
    }

    private volatile boolean shouldStop = false;

    public void readData(DataCallback callback) {
        // Read data from the InputStream on a separate thread

        new Thread(() -> {
            StringBuilder dataBuilder = new StringBuilder(); //To "store" data
            try {
                byte[] buffer = new byte[1024];  //Buffer to store incoming data
                int bytes;
                while ((bytes = inputStream.read(buffer)) != -1) { //Read from InputStream

                    String data = new String(buffer, 0, bytes); //Convert bytes to String
                    dataBuilder.append(data); //Append to StringBuilder
                    handler.post(() -> {
                        if (callback != null) {
                            callback.onDataReceived(data); //Send data to callback
                        }
                    });
                }

                if (!shouldStop && callback != null) {
                    handler.post(() -> callback.onDataReceived(dataBuilder.toString()));
                }
            } catch (Exception e) {
                Log.e(TAG, "Error in readData(): " + e.getMessage());
                e.printStackTrace();
            }
        }).start();
    }

    public void stopReading() {
        shouldStop = true;
        disconnect();
    }

    public void startReading() {
        shouldStop = false;
    }

    @Override
    public void onDataReceived(String data) {

    }

    public void showConnectionUI(View view, int visibility) {
        if (view != null) {
            view.setVisibility(visibility);
        }
    }

    public boolean isConnected() {
        return isConnected;
    }
}