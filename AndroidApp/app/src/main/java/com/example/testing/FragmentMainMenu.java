package com.example.testing;

import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

public class FragmentMainMenu extends Fragment {

    private final String TAG = "FragmentMainMenu";

    private static final String ARG_PARAM1 = "param1";
    private static final String ARG_PARAM2 = "param2";
    private String mParam2, mParam1;

    public FragmentMainMenu() {}

    private static FragmentMainMenu INSTANCE = null;

    public static FragmentMainMenu newInstance(String param1, String param2) {
        FragmentMainMenu fragment = new FragmentMainMenu();
        Bundle args = new Bundle();
        args.putString(ARG_PARAM1, param1);
        args.putString(ARG_PARAM2, param2);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        INSTANCE = this;

        if (getArguments() != null) {
            mParam1 = getArguments().getString(ARG_PARAM1);
            mParam2 = getArguments().getString(ARG_PARAM2);
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        return inflater.inflate(R.layout.fragment_main_menu, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        SharedViewmodel sharedViewmodel = new ViewModelProvider(requireActivity()).get(SharedViewmodel.class);

        Button goButton = view.findViewById(R.id.button3);

        Button savedDataButton = view.findViewById(R.id.button6);

        goButton.setOnClickListener(v -> {

            ConnectionManager.getInstance().sendData("1");

            if (ConnectionManager.getInstance().isConnected()) {
                getParentFragmentManager().beginTransaction()
                        .setReorderingAllowed(true)
                        .setCustomAnimations(
                                R.anim.slide_in,
                                R.anim.slide_out,
                                R.anim.slide_in,
                                R.anim.slide_out
                        ).replace(R.id.rootContainer, new FragmentShowLiveData()).addToBackStack(null).commit();
            } else {
                ConnectionManager.getInstance().enableBluetooth(getActivity());
                ConnectionManager.getInstance().connectToPI();

                ConnectionManager.getInstance().startReading();
                ConnectionManager.getInstance().sendData("1");

                if (ConnectionManager.getInstance().isConnected()) {
                    Log.d(TAG, "onViewCreated: Connected");
                    ConnectionManager.getInstance().readData(data -> {
                        if (data != null && !data.isEmpty()) {

                            data = data.trim();
                            Log.d(TAG, "Received data: " + data);

                            sharedViewmodel.updateColorID(Integer.parseInt(data));

                        } else {
                            Log.d(TAG, "Data is null or empty");
                        }
                    });

                    getParentFragmentManager().beginTransaction().setCustomAnimations(
                            R.anim.slide_in,
                            R.anim.fade_out,
                            R.anim.fade_in,
                            R.anim.slide_in
                    ).replace(R.id.rootContainer, new FragmentShowLiveData()).commit();

                } else {
                    Toast.makeText(getContext(), "Device is not connected!", Toast.LENGTH_LONG).show();
                    Log.d(TAG, "onViewCreated: Nu este conectat");
                }
            }
        });

        savedDataButton.setOnClickListener(v -> {
            getParentFragmentManager().beginTransaction()
                    .setReorderingAllowed(true)
                    .setCustomAnimations(
                            R.anim.fade_in,
                            R.anim.fade_out,
                            R.anim.fade_in,
                            R.anim.fade_out
            ).replace(R.id.rootContainer, new FragmentSavedDataMenu()).addToBackStack(null).commit();
        });
    }
}