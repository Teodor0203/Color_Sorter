package com.example.testing;

import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.google.android.gms.maps.GoogleMap;

public class FragmentShowSavedData extends Fragment {

    private String savedDataName;
    private ProgressBar progressBar;
    SaveDataManager saveDataManager = new SaveDataManager();


    private static final String ARG_PARAM1 = "param1";
    private static final String ARG_PARAM2 = "param2";

    private String mParam1;
    private String mParam2;

    public FragmentShowSavedData(){
        // Required empty public constructor}
    }

    public FragmentShowSavedData(String savedDataName) {
        this.savedDataName = savedDataName;
        Log.d("SavedDataMenu", "FragmentShowSavedData: BUTTON NAME" + savedDataName);
    }

    public static FragmentShowSavedData newInstance(String param1, String param2) {
        String savedDataName = "";
        FragmentShowSavedData fragment = new FragmentShowSavedData();
        Bundle args = new Bundle();
        args.putString(ARG_PARAM1, param1);
        args.putString(ARG_PARAM2, param2);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            mParam1 = getArguments().getString(ARG_PARAM1);
            mParam2 = getArguments().getString(ARG_PARAM2);
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_show_saved_data, container, false);

        return view;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        if(progressBar != null)
        {
            progressBar.setVisibility(View.INVISIBLE);
        }

        TextView redColorText = getView().findViewById(R.id.colorRed);
        TextView blueColorText = getView().findViewById(R.id.colorBlue);
        TextView yellowColorText = getView().findViewById(R.id.colorYellow);
        TextView pinkColorText = getView().findViewById(R.id.colorPink);

        saveDataManager.loadSavedData(getContext(), savedDataName, redColorText, blueColorText, yellowColorText, pinkColorText);
        Log.d("SavedDataMenu", "called");

    }
}