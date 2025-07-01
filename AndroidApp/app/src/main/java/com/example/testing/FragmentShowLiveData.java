package com.example.testing;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

/**
 * A simple {@link Fragment} subclass.
 * Use the {@link FragmentShowLiveData#newInstance} factory method to
 * create an instance of this fragment.
 */
public class FragmentShowLiveData extends Fragment {

    private final String TAG = "LiveData";

    private int countRed = 0;
    private int countPink = 0;
    private int countBlue = 0;
    private int countYellow = 0;

    private DialogInterface.OnClickListener dialogClickListener;

    private Button stopButton;
    private Button startButton;

    private Button endButton;
    private static final String ARG_PARAM1 = "param1";
    private static final String ARG_PARAM2 = "param2";

    // TODO: Rename and change types of parameters
    private String mParam1;
    private String mParam2;

    public FragmentShowLiveData() {
        // Required empty public constructor
    }

    public static FragmentShowLiveData newInstance(String param1, String param2) {
        FragmentShowLiveData fragment = new FragmentShowLiveData();
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
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        return inflater.inflate(R.layout.fragment_show_live_data, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        SharedViewmodel sharedViewModel = new ViewModelProvider(requireActivity()).get(SharedViewmodel.class);

        stopButton = view.findViewById(R.id.stopButton);
        startButton = view.findViewById(R.id.startButton);
        endButton = view.findViewById(R.id.endButton);

        if(startButton != null)
        {
            startButton.setVisibility(View.INVISIBLE);
        }

        TextView redColorTextView = view.findViewById(R.id.colorRed);
        TextView yellowColorTextView = view.findViewById(R.id.colorYellow);
        TextView blueColorTextView = view.findViewById(R.id.colorBlue);
        TextView pinkColorTextView = view.findViewById(R.id.colorPink);

        sharedViewModel.getDataLiveData().observe(getViewLifecycleOwner(), data -> {

            int colorID = data.getColorID();

            switch (colorID) {
                case 0:
                    countRed++;
                    break;
                case 1:
                    countPink++;
                    break;
                case 2:
                    countBlue++;
                    break;
                case 3:
                    countYellow++;
                    break;
                default:
                    Log.d(TAG, "Unknown color code: " + data);
            }

            // Updates UI
            if (redColorTextView != null)
                redColorTextView.setText("Red: " + countRed);
            if (yellowColorTextView != null)
                yellowColorTextView.setText("Green: " + countPink);
            if (blueColorTextView != null)
                blueColorTextView.setText("Blue: " + countBlue);
            if (pinkColorTextView != null)
                pinkColorTextView.setText("Yellow: " + countYellow);

            stopButton.setOnClickListener(view1 -> {
                ConnectionManager.getInstance().sendData("0");

                if(startButton != null)
                    startButton.setVisibility(View.VISIBLE);

                if(stopButton != null)
                    stopButton.setVisibility(View.INVISIBLE);
            });


            startButton.setOnClickListener(view1 -> {
                ConnectionManager.getInstance().sendData("1");

                if(startButton != null)
                    startButton.setVisibility(View.INVISIBLE);

                if(stopButton != null)
                    stopButton.setVisibility(View.VISIBLE);
            });

            endButton.setOnClickListener(view1 -> {
                ConnectionManager.getInstance().sendData("0");

                showDialogBox();

            });
        });
    }

    public void showDialogBox() {

        if (getActivity() != null && isAdded()) {

            //Create a listener for handling button clicks on the dialog
            dialogClickListener = new DialogInterface.OnClickListener() {
                @SuppressLint("ShowToast")
                @Override
                public void onClick(DialogInterface dialogInterface, int which) {

                    //The switch statement handles the actions based on the button pressed
                    switch (which) {
                        case DialogInterface.BUTTON_POSITIVE:
                            Toast.makeText(getContext(), "Data was saved", Toast.LENGTH_LONG).show();
                            SaveDataManager.getInstance().saveDataToFile(getContext(), (("Saved data " + SaveDataManager.getInstance().loadIndexFromFile(getContext()))), countRed, countBlue, countYellow, countPink);
                            getParentFragmentManager().beginTransaction().setCustomAnimations(
                                    R.anim.slide_in,
                                    R.anim.fade_out,
                                    R.anim.fade_in,
                                    R.anim.slide_in
                            ).replace(R.id.rootContainer, new FragmentMainMenu()).commit();
                            break;
                        case DialogInterface.BUTTON_NEGATIVE:
                            getParentFragmentManager().beginTransaction().setCustomAnimations(
                                    R.anim.slide_in,
                                    R.anim.fade_out,
                                    R.anim.fade_in,
                                    R.anim.slide_in
                            ).replace(R.id.rootContainer, new FragmentMainMenu()).commit();
                            Toast.makeText(getContext(), "Data was not saved", Toast.LENGTH_LONG).show();

                            dialogInterface.dismiss();
                    }
                }
            };

            AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());

            // Set the message and the buttons (Yes/No)
            builder.setMessage("Do you want to save?")
                    .setPositiveButton("Yes", dialogClickListener) // Set "Yes" button action
                    .setNegativeButton("No", dialogClickListener) // Set "No" button action
                    .show(); // Show the dialog
        }
    }
}